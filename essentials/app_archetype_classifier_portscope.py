#!/usr/bin/env python3
"""
PortScope Application Architecture Classifier
Version: 2.0
Author: PortScope Team (Enhanced from original by Ajay Pillai)
Description: Enhanced classifier that integrates with PortScope to identify application
            architecture patterns based on port analysis and service discovery.
"""

import yaml
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ClassificationResult:
    """Result of architecture classification"""
    archetype: str
    confidence: float
    score: int
    evidence: List[str] = field(default_factory=list)
    risk_level: str = "unknown"
    risk_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    port_summary: Dict[str, Any] = field(default_factory=dict)
    alternative_matches: List[Tuple[str, float]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class ArchetypeClassifier:
    """Classify application architectures based on port patterns and service indicators"""
    
    def __init__(self, config_path: str = "archetype_templates_portscope.yaml"):
        """Initialize classifier with configuration"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.port_db = self.config.get('port_database', {})
        self.archetypes = self.config.get('archetypes', {})
        self.rules = self.config.get('classification_rules', {})
        self.risk_config = self.config.get('risk_assessment', {})
        self.service_categories = self.config.get('service_categories', {})
        self._build_port_lookup()
        
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Config file not found at {self.config_path}, using defaults")
                return self._get_default_config()
            
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Return a minimal default configuration"""
        return {
            'archetypes': {
                'unknown': {
                    'name': 'Unknown',
                    'description': 'Unable to determine architecture',
                    'indicators': {}
                }
            },
            'classification_rules': {
                'confidence_thresholds': {'high': 0.8, 'medium': 0.6, 'low': 0.4},
                'scoring_weights': {
                    'required_ports_match': 10,
                    'optional_ports_match': 3,
                    'port_pattern_match': 5,
                    'required_category_match': 8,
                    'forbidden_violation': -15
                }
            },
            'risk_assessment': {
                'port_risks': {
                    'critical': {'ports': [23], 'score': 10},
                    'high': {'ports': [445, 3389], 'score': 7},
                    'medium': {'ports': [80], 'score': 4},
                    'low': {'ports': [443], 'score': 1}
                }
            }
        }
    
    def _build_port_lookup(self):
        """Build a fast lookup table for ports"""
        self.port_lookup = {}
        for section in ['well_known', 'common_services']:
            if section in self.port_db:
                for port, info in self.port_db[section].items():
                    self.port_lookup[port] = info
    
    def classify_from_dataframe(self, df: pd.DataFrame) -> ClassificationResult:
        """Classify architecture from PortScope analyzed DataFrame"""
        # Extract port and service information
        port_info = self._extract_port_info(df)
        
        # Score each archetype
        archetype_scores = {}
        for arch_name, arch_config in self.archetypes.items():
            score, evidence = self._score_archetype(port_info, arch_config)
            archetype_scores[arch_name] = {
                'score': score,
                'evidence': evidence,
                'config': arch_config
            }
        
        # Select best match
        if not archetype_scores:
            return self._create_unknown_result(port_info)
        
        best_match = max(archetype_scores.items(), key=lambda x: x[1]['score'])
        arch_name = best_match[0]
        arch_data = best_match[1]
        
        # Check minimum score threshold
        min_score = self.rules.get('fallback_classification', {}).get('min_score_for_classification', 15)
        if arch_data['score'] < min_score:
            arch_name = 'unknown'
            arch_data = archetype_scores.get('unknown', {'score': 0, 'evidence': [], 'config': {}})
        
        # Calculate confidence
        confidence = self._calculate_confidence(arch_data['score'])
        
        # Assess risk
        risk_level, risk_score = self._assess_risk(port_info, arch_data['config'])
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            port_info, arch_name, risk_level
        )
        
        # Get alternative matches
        alternatives = [(name, self._calculate_confidence(data['score'])) 
                       for name, data in archetype_scores.items() 
                       if name != arch_name and data['score'] > 0]
        alternatives.sort(key=lambda x: x[1], reverse=True)
        
        # Add metadata
        metadata = {
            'total_archetypes_evaluated': len(archetype_scores),
            'config_file': str(self.config_path),
            'diagram_stub': arch_data['config'].get('diagram_stub', ''),
            'min_score_threshold': min_score
        }
        
        return ClassificationResult(
            archetype=arch_name,
            confidence=confidence,
            score=arch_data['score'],
            evidence=arch_data['evidence'][:10],  # Limit evidence items
            risk_level=risk_level,
            risk_score=risk_score,
            recommendations=recommendations,
            port_summary=self._create_port_summary(port_info),
            alternative_matches=alternatives[:3],
            metadata=metadata
        )
    
    def _extract_port_info(self, df: pd.DataFrame) -> Dict:
        """Extract port and service information from DataFrame"""
        info = {
            'ports': [],
            'services': [],
            'categories': [],
            'protocols': {},
            'risk_levels': {},
            'host_count': 0,
            'total_ports': 0,
            'identified_ports': 0,
            'port_ranges': {},
            'unique_ports': set(),
            'service_to_ports': defaultdict(list)
        }
        
        if df.empty:
            return info
        
        # Extract basic information
        info['ports'] = df['port'].unique().tolist() if 'port' in df.columns else []
        info['unique_ports'] = set(info['ports'])
        info['total_ports'] = len(df)
        
        # Extract services if available
        if 'service_name' in df.columns and 'identified' in df.columns:
            identified_df = df[df['identified'] == True]
            info['services'] = identified_df['service_name'].unique().tolist()
            info['identified_ports'] = identified_df.shape[0]
            
            # Map services to ports
            for _, row in identified_df.iterrows():
                if pd.notna(row['service_name']):
                    info['service_to_ports'][row['service_name']].append(row['port'])
        
        # Extract categories
        if 'category' in df.columns:
            info['categories'] = df[df['category'].notna()]['category'].unique().tolist()
        
        # Protocol distribution
        if 'protocol' in df.columns:
            info['protocols'] = df['protocol'].value_counts().to_dict()
        
        # Risk distribution
        if 'risk_level' in df.columns:
            info['risk_levels'] = df[df['risk_level'].notna()]['risk_level'].value_counts().to_dict()
        
        # Host count
        if 'ip_address' in df.columns:
            info['host_count'] = df['ip_address'].nunique()
        elif 'host' in df.columns:
            info['host_count'] = df['host'].nunique()
        
        # Analyze port ranges
        info['port_ranges'] = self._analyze_port_ranges(info['ports'])
        
        return info
    
    def _analyze_port_ranges(self, ports: List[int]) -> Dict:
        """Analyze distribution of ports across ranges"""
        ranges = {
            'well_known': 0,
            'registered': 0,
            'dynamic': 0,
            'custom_ranges': defaultdict(int)
        }
        
        for port in ports:
            if port < 1024:
                ranges['well_known'] += 1
            elif port < 49152:
                ranges['registered'] += 1
            else:
                ranges['dynamic'] += 1
            
            # Check custom ranges (e.g., 3000-3100 for microservices)
            if 3000 <= port <= 3100:
                ranges['custom_ranges']['microservice_range'] += 1
            elif 8000 <= port <= 9000:
                ranges['custom_ranges']['app_server_range'] += 1
        
        return dict(ranges)
    
    def _score_archetype(self, port_info: Dict, arch_config: Dict) -> Tuple[int, List[str]]:
        """Score an archetype based on port information"""
        score = 0
        evidence = []
        weights = self.rules.get('scoring_weights', {})
        indicators = arch_config.get('indicators', {})
        
        # Check ports
        if 'ports' in indicators:
            # Required ports
            required = indicators['ports'].get('required', [])
            if required:
                matches = [p for p in required if p in port_info['unique_ports']]
                if matches:
                    points = len(matches) * weights.get('required_ports_match', 10)
                    score += points
                    evidence.append(f"Required ports found: {matches} (+{points})")
                else:
                    # Missing required ports is a strong negative signal
                    score -= 5
                    evidence.append(f"Missing required ports: {required} (-5)")
            
            # Required any (at least one from the list)
            required_any = indicators['ports'].get('required_any', [])
            if required_any:
                for port_group in required_any:
                    if isinstance(port_group, list):
                        if any(p in port_info['unique_ports'] for p in port_group):
                            points = weights.get('required_any_match', 8)
                            score += points
                            matched = [p for p in port_group if p in port_info['unique_ports']]
                            evidence.append(f"Required group matched: {matched} (+{points})")
                    elif port_group in port_info['unique_ports']:
                        points = weights.get('required_any_match', 8)
                        score += points
                        evidence.append(f"Required port found: {port_group} (+{points})")
            
            # Optional ports
            optional = indicators['ports'].get('optional', [])
            if optional:
                matches = [p for p in optional if p in port_info['unique_ports']]
                if matches:
                    points = len(matches) * weights.get('optional_ports_match', 3)
                    score += points
                    evidence.append(f"Optional ports found: {matches[:5]} (+{points})")
            
            # Forbidden ports
            forbidden = indicators['ports'].get('forbidden', [])
            if forbidden:
                violations = [p for p in forbidden if p in port_info['unique_ports']]
                if violations:
                    points = len(violations) * weights.get('forbidden_violation', -15)
                    score += points
                    evidence.append(f"Forbidden ports found: {violations} ({points})")
        
        # Check port patterns
        if 'port_patterns' in indicators:
            for pattern in indicators['port_patterns']:
                matched, pattern_desc = self._check_port_pattern(port_info, pattern)
                if matched:
                    points = weights.get('port_pattern_match', 5)
                    score += points
                    evidence.append(f"Port pattern matched: {pattern_desc} (+{points})")
        
        # Check service categories
        if 'services' in indicators:
            # Required categories
            required_cats = indicators['services'].get('required_categories', [])
            for cat in required_cats:
                if cat in port_info['categories']:
                    points = weights.get('required_category_match', 8)
                    score += points
                    evidence.append(f"Required category '{cat}' found (+{points})")
                else:
                    score -= 3
                    evidence.append(f"Missing required category '{cat}' (-3)")
            
            # Required any categories
            required_any_cats = indicators['services'].get('required_categories_any', [])
            if required_any_cats and any(cat in port_info['categories'] for cat in required_any_cats):
                points = weights.get('required_category_match', 8)
                score += points
                matched_cats = [c for c in required_any_cats if c in port_info['categories']]
                evidence.append(f"Required category matched: {matched_cats} (+{points})")
            
            # Optional categories
            optional_cats = indicators['services'].get('optional_categories', [])
            for cat in optional_cats:
                if cat in port_info['categories']:
                    points = weights.get('optional_category_match', 2)
                    score += points
                    evidence.append(f"Optional category '{cat}' found (+{points})")
            
            # Forbidden categories
            forbidden_cats = indicators['services'].get('forbidden_categories', [])
            for cat in forbidden_cats:
                if cat in port_info['categories']:
                    points = weights.get('forbidden_violation', -15)
                    score += points
                    evidence.append(f"Forbidden category '{cat}' found ({points})")
        
        # Check host count
        if 'host_count' in indicators and port_info['host_count'] > 0:
            min_hosts = indicators['host_count'].get('min', 0)
            max_hosts = indicators['host_count'].get('max', float('inf'))
            if min_hosts <= port_info['host_count'] <= max_hosts:
                points = weights.get('host_count_match', 4)
                score += points
                evidence.append(f"Host count matches ({port_info['host_count']}) (+{points})")
            else:
                evidence.append(f"Host count mismatch ({port_info['host_count']}) (0)")
        
        # Check traffic patterns (if available in metadata)
        if 'traffic' in indicators:
            traffic = indicators['traffic']
            if traffic.get('pattern'):
                # This would require additional traffic analysis
                # Placeholder for now
                pass
        
        return max(0, score), evidence
    
    def _check_port_pattern(self, port_info: Dict, pattern: Dict) -> Tuple[bool, str]:
        """Check if ports match a pattern"""
        if 'range' in pattern:
            port_range = pattern['range']
            min_count = pattern.get('min_count', 1)
            max_count = pattern.get('max_count', float('inf'))
            
            ports_in_range = [p for p in port_info['ports'] 
                            if port_range[0] <= p <= port_range[1]]
            
            count = len(ports_in_range)
            if min_count <= count <= max_count:
                return True, f"Range {port_range} has {count} ports"
        
        if 'category' in pattern:
            category = pattern['category']
            min_count = pattern.get('min_count', 1)
            
            # Count ports in this category
            cat_count = 0
            for port in port_info['ports']:
                port_info_db = self.port_lookup.get(port, {})
                if port_info_db.get('category') == category:
                    cat_count += 1
            
            if cat_count >= min_count:
                return True, f"Category '{category}' has {cat_count} ports"
        
        if 'exact' in pattern and pattern['exact']:
            # Exact port match only
            if 'range' in pattern:
                expected = set(range(pattern['range'][0], pattern['range'][1] + 1))
                if port_info['unique_ports'] == expected:
                    return True, "Exact port match"
        
        return False, ""
    
    def _calculate_confidence(self, score: int) -> float:
        """Calculate confidence score based on points"""
        if score <= 0:
            return 0.0
        elif score >= 60:
            return min(0.95, 0.8 + (score - 60) / 100.0)
        elif score >= 40:
            return 0.7 + (score - 40) / 100.0
        elif score >= 25:
            return 0.5 + (score - 25) / 60.0
        elif score >= 15:
            return 0.3 + (score - 15) / 50.0
        else:
            return score / 50.0
    
    def _assess_risk(self, port_info: Dict, arch_config: Dict) -> Tuple[str, float]:
        """Assess security risk based on ports and architecture"""
        risk_score = 0.0
        risk_details = []
        
        port_risks = self.risk_config.get('port_risks', {})
        
        # Check port-based risks
        for risk_level, risk_data in port_risks.items():
            risk_ports = set(risk_data.get('ports', []))
            found = port_info['unique_ports'] & risk_ports
            if found:
                points = len(found) * risk_data.get('score', 0)
                risk_score += points
                risk_details.append(f"{risk_level} risk ports: {list(found)[:5]}")
        
        # Add category-based risks
        category_risks = self.risk_config.get('category_risks', {})
        for cat in port_info['categories']:
            cat_risk = category_risks.get(cat, 0)
            if cat_risk > 0:
                risk_score += cat_risk
                risk_details.append(f"Category '{cat}' risk: {cat_risk}")
        
        # Apply architecture modifier
        modifier = arch_config.get('risk_score_modifier', 1.0)
        risk_score *= modifier
        
        # Consider existing risk levels from port analysis
        if 'critical' in port_info.get('risk_levels', {}):
            risk_score += port_info['risk_levels']['critical'] * 5
        if 'high' in port_info.get('risk_levels', {}):
            risk_score += port_info['risk_levels']['high'] * 3
        
        # Determine risk level
        if risk_score >= 40:
            return "critical", risk_score
        elif risk_score >= 25:
            return "high", risk_score
        elif risk_score >= 15:
            return "medium", risk_score
        elif risk_score >= 5:
            return "low", risk_score
        else:
            return "minimal", risk_score
    
    def _generate_recommendations(self, port_info: Dict, 
                                 archetype: str, risk_level: str) -> List[str]:
        """Generate security and optimization recommendations"""
        recommendations = []
        
        # Critical security recommendations
        critical_ports = {
            23: "🔴 CRITICAL: Telnet (port 23) is unencrypted. Replace with SSH immediately!",
            512: "🔴 CRITICAL: rexec (port 512) has no security. Disable immediately!",
            513: "🔴 CRITICAL: rlogin (port 513) is insecure. Replace with SSH!",
            514: "🔴 CRITICAL: rsh (port 514) is insecure. Replace with SSH!"
        }
        
        for port, rec in critical_ports.items():
            if port in port_info['unique_ports']:
                recommendations.append(rec)
        
        # High risk recommendations
        high_risk_ports = {
            21: "⚠️ HIGH: FTP (port 21) transmits credentials in plaintext. Use SFTP or FTPS",
            445: "⚠️ HIGH: SMB (port 445) is often targeted. Ensure latest security patches",
            3389: "⚠️ HIGH: RDP (port 3389) is a common attack vector. Use VPN + MFA",
            5900: "⚠️ HIGH: VNC (port 5900) has weak authentication. Use SSH tunneling",
            1433: "⚠️ HIGH: SQL Server (port 1433) exposed. Use firewall rules + encryption",
            3306: "⚠️ HIGH: MySQL (port 3306) exposed. Restrict access + use SSL",
            5432: "⚠️ HIGH: PostgreSQL (port 5432) exposed. Implement pg_hba.conf rules",
            6379: "⚠️ HIGH: Redis (port 6379) often unsecured. Enable AUTH + bind to localhost",
            27017: "⚠️ HIGH: MongoDB (port 27017) exposed. Enable authentication + TLS",
            11211: "⚠️ HIGH: Memcached (port 11211) has no auth. Bind to localhost only"
        }
        
        for port, rec in high_risk_ports.items():
            if port in port_info['unique_ports'] and len(recommendations) < 8:
                recommendations.append(rec)
        
        # Architecture-specific recommendations
        arch_recommendations = {
            "monolithic": [
                "📊 Consider implementing caching layer to improve performance",
                "🔄 Plan migration to microservices for better scalability",
                "🛡️ Implement API rate limiting and authentication"
            ],
            "microservices": [
                "🌐 Implement service mesh (Istio/Linkerd) for better observability",
                "🔐 Use mutual TLS between services",
                "📊 Add distributed tracing (Jaeger/Zipkin)"
            ],
            "three_tier": [
                "⚖️ Add load balancer for high availability",
                "💾 Implement database read replicas",
                "🔒 Use web application firewall (WAF)"
            ],
            "client_server": [
                "🔐 Implement row-level security in database",
                "🌐 Consider adding API layer for modern clients",
                "📱 Plan migration to web-based architecture"
            ],
            "event_driven": [
                "📬 Implement message encryption and signing",
                "🔄 Add circuit breakers for resilience",
                "📊 Monitor message queue depths and latencies"
            ],
            "serverless": [
                "🔐 Use API Gateway authentication",
                "📊 Implement distributed tracing",
                "💰 Monitor and optimize function execution costs"
            ],
            "edge_cloud_hybrid": [
                "🔒 Implement end-to-end encryption for IoT devices",
                "📡 Use certificate pinning for device authentication",
                "🛡️ Deploy edge security gateway"
            ]
        }
        
        if archetype in arch_recommendations and len(recommendations) < 10:
            for rec in arch_recommendations[archetype]:
                if len(recommendations) < 10:
                    recommendations.append(rec)
        
        # General security recommendations
        if risk_level in ["critical", "high"] and len(recommendations) < 10:
            general_recs = [
                "🛡️ Implement network segmentation and firewalls",
                "🔐 Enable multi-factor authentication (MFA)",
                "📝 Regular security audits and penetration testing",
                "🔄 Keep all services updated with latest patches",
                "📊 Implement comprehensive logging and monitoring"
            ]
            for rec in general_recs:
                if len(recommendations) < 10:
                    recommendations.append(rec)
        
        # HTTP/HTTPS recommendations
        http_ports = {80, 8080, 8000, 8001, 8008, 8081, 8088, 8090}
        if http_ports & port_info['unique_ports']:
            recommendations.append("🔒 Enable HTTPS for all HTTP services")
        
        # Documentation recommendation
        if port_info['identified_ports'] < port_info['total_ports'] * 0.7:
            unidentified = port_info['total_ports'] - port_info['identified_ports']
            recommendations.append(f"📝 Document or close {unidentified} unidentified ports")
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _create_port_summary(self, port_info: Dict) -> Dict:
        """Create a summary of port analysis"""
        summary = {
            'total_ports': port_info['total_ports'],
            'unique_ports': len(port_info['unique_ports']),
            'identified_ports': port_info['identified_ports'],
            'identification_rate': 0.0,
            'unique_services': len(port_info['services']),
            'service_categories': port_info['categories'],
            'port_ranges': port_info['port_ranges'],
            'top_protocols': dict(Counter(port_info['protocols']).most_common(3)),
            'risk_distribution': port_info['risk_levels'],
            'host_distribution': {
                'unique_hosts': port_info['host_count'],
                'ports_per_host': port_info['total_ports'] / max(1, port_info['host_count'])
            }
        }
        
        if port_info['total_ports'] > 0:
            summary['identification_rate'] = round(
                (port_info['identified_ports'] / port_info['total_ports']) * 100, 1
            )
        
        return summary
    
    def _create_unknown_result(self, port_info: Dict) -> ClassificationResult:
        """Create a result for unknown architecture"""
        return ClassificationResult(
            archetype="unknown",
            confidence=0.0,
            score=0,
            evidence=["Unable to determine architecture pattern"],
            risk_level="unknown",
            risk_score=0.0,
            recommendations=["Perform detailed analysis of the application architecture"],
            port_summary=self._create_port_summary(port_info),
            alternative_matches=[]
        )
    
    def generate_report(self, result: ClassificationResult) -> str:
        """Generate a detailed text report"""
        report = []
        report.append("=" * 70)
        report.append(" " * 15 + "PORTSCOPE ARCHITECTURE CLASSIFICATION REPORT")
        report.append("=" * 70)
        
        # Timestamp
        report.append(f"\n📅 Analysis Date: {result.timestamp}")
        
        # Primary classification
        confidence_emoji = "🟢" if result.confidence > 0.7 else "🟡" if result.confidence > 0.4 else "🔴"
        report.append(f"\n🏗️  IDENTIFIED ARCHITECTURE: {result.archetype.upper()}")
        report.append(f"   {confidence_emoji} Confidence: {result.confidence:.1%} (Score: {result.score})")
        
        # Architecture description
        if result.archetype in self.archetypes:
            desc = self.archetypes[result.archetype].get('description', '')
            if desc:
                report.append(f"   📝 Description: {desc}")
        
        # Alternative matches
        if result.alternative_matches:
            report.append("\n📊 Alternative Architectures:")
            for i, (arch, conf) in enumerate(result.alternative_matches, 1):
                conf_emoji = "🟢" if conf > 0.7 else "🟡" if conf > 0.4 else "🔴"
                report.append(f"   {i}. {arch}: {conf_emoji} {conf:.1%} confidence")
        
        # Evidence
        if result.evidence:
            report.append("\n🔍 Classification Evidence:")
            for evidence in result.evidence[:7]:
                report.append(f"   • {evidence}")
        
        # Risk assessment
        risk_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "minimal": "✅",
            "unknown": "❓"
        }
        report.append(f"\n⚠️  SECURITY RISK ASSESSMENT")
        report.append(f"   {risk_emoji.get(result.risk_level, '❓')} Risk Level: {result.risk_level.upper()}")
        report.append(f"   📊 Risk Score: {result.risk_score:.1f}")
        
        # Port summary
        if result.port_summary:
            report.append("\n📈 Port Analysis Summary:")
            summary = result.port_summary
            report.append(f"   • Total Ports Scanned: {summary.get('total_ports', 0)}")
            report.append(f"   • Unique Ports Found: {summary.get('unique_ports', 0)}")
            report.append(f"   • Services Identified: {summary.get('identified_ports', 0)} ({summary.get('identification_rate', 0)}%)")
            report.append(f"   • Unique Services: {summary.get('unique_services', 0)}")
            
            if summary.get('service_categories'):
                report.append(f"   • Service Categories: {', '.join(summary['service_categories'][:5])}")
            
            if summary.get('port_ranges'):
                ranges = summary['port_ranges']
                report.append(f"   • Port Distribution:")
                report.append(f"     - Well-Known (0-1023): {ranges.get('well_known', 0)}")
                report.append(f"     - Registered (1024-49151): {ranges.get('registered', 0)}")
                report.append(f"     - Dynamic (49152+): {ranges.get('dynamic', 0)}")
        
        # Recommendations
        if result.recommendations:
            report.append("\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(result.recommendations, 1):
                report.append(f"   {rec}")
        
        # Footer
        report.append("\n" + "-" * 70)
        report.append("📌 Note: This analysis is based on port patterns and may not reflect")
        report.append("   the complete architecture. Consider additional factors like data")
        report.append("   flow, deployment topology, and business logic distribution.")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def export_result(self, result: ClassificationResult, 
                     output_path: str, format: str = "json") -> bool:
        """Export classification result to file"""
        try:
            output_file = Path(output_path)
            
            if format == "json":
                result_dict = {
                    'archetype': result.archetype,
                    'confidence': result.confidence,
                    'score': result.score,
                    'evidence': result.evidence,
                    'risk_level': result.risk_level,
                    'risk_score': result.risk_score,
                    'recommendations': result.recommendations,
                    'port_summary': result.port_summary,
                    'alternatives': result.alternative_matches,
                    'metadata': result.metadata,
                    'timestamp': result.timestamp
                }
                
                with open(output_file, 'w') as f:
                    json.dump(result_dict, f, indent=2)
                    
            elif format == "yaml":
                result_dict = {
                    'classification': {
                        'archetype': result.archetype,
                        'confidence': float(result.confidence),
                        'score': int(result.score)
                    },
                    'risk_assessment': {
                        'level': result.risk_level,
                        'score': float(result.risk_score)
                    },
                    'evidence': result.evidence,
                    'recommendations': result.recommendations,
                    'summary': result.port_summary
                }
                
                with open(output_file, 'w') as f:
                    yaml.dump(result_dict, f, default_flow_style=False)
                    
            elif format == "txt":
                report = self.generate_report(result)
                with open(output_file, 'w') as f:
                    f.write(report)
            
            logger.info(f"Exported classification result to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export result: {e}")
            return False

def integrate_with_portscope(portscope_analyzer, csv_path: str, 
                            config_path: str = "archetype_templates_portscope.yaml") -> Tuple:
    """Integration function for PortScope"""
    # Use PortScope to analyze ports
    df = portscope_analyzer.parse_csv(csv_path)
    analyzed_df = portscope_analyzer.analyze_ports(df)
    
    # Classify architecture
    classifier = ArchetypeClassifier(config_path)
    result = classifier.classify_from_dataframe(analyzed_df)
    
    # Generate report
    report = classifier.generate_report(result)
    
    return result, report, analyzed_df

# Example usage and testing
if __name__ == "__main__":
    # Create sample data for testing
    print("Creating sample data for testing...")
    
    # Test different architecture patterns
    test_cases = {
        "microservices": {
            'port': [22, 443, 6443, 2375, 3000, 3001, 3002, 3003, 3004, 
                    9090, 9200, 5672, 6379, 8500],
            'service_name': ['SSH', 'HTTPS', 'Kubernetes', 'Docker', 'Node.js', 
                           'Node.js', 'Node.js', 'Node.js', 'Node.js',
                           'Prometheus', 'Elasticsearch', 'AMQP', 'Redis', 'Consul-HTTP'],
            'category': ['remote_access', 'web', 'container', 'container', 'web',
                        'web', 'web', 'web', 'web',
                        'monitoring', 'search', 'messaging', 'cache', 'coordination']
        },
        "monolithic": {
            'port': [8080, 3306],
            'service_name': ['HTTP-Proxy', 'MySQL'],
            'category': ['web', 'database']
        },
        "event_driven": {
            'port': [9092, 9093, 5672, 8080, 3306, 6379],
            'service_name': ['Kafka', 'Kafka-SSL', 'AMQP', 'HTTP-Proxy', 'MySQL', 'Redis'],
            'category': ['messaging', 'messaging', 'messaging', 'web', 'database', 'cache']
        }
    }
    
    classifier = ArchetypeClassifier()
    
    for test_name, test_data in test_cases.items():
        print(f"\n{'='*70}")
        print(f"Testing {test_name.upper()} pattern")
        print('='*70)
        
        # Create DataFrame
        df = pd.DataFrame({
            'port': test_data['port'],
            'protocol': ['TCP'] * len(test_data['port']),
            'service_name': test_data['service_name'],
            'category': test_data['category'],
            'risk_level': ['medium'] * len(test_data['port']),
            'identified': [True] * len(test_data['port']),
            'ip_address': [f'192.168.1.{i%5 + 1}' for i in range(len(test_data['port']))]
        })
        
        # Classify
        result = classifier.classify_from_dataframe(df)
        
        # Generate and print report
        report = classifier.generate_report(result)
        print(report)
        
        # Export results
        classifier.export_result(result, f"test_{test_name}_result.json", "json")
    
    print("\n" + "="*70)
    print("Testing complete! Check the generated JSON files for detailed results.")
    print("="*70)