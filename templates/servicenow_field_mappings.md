
# ServiceNow Field Mapping Documentation

## Overview
This document provides comprehensive field mappings between ServiceNow CMDB tables and the metadata discovery framework.

## Required Export Fields by Table

### 1. Applications (cmdb_ci_appl)
**Purpose**: Core application information for metadata discovery and visualization

**Critical Fields**:
- `sys_id` - Primary key for relationships
- `name` - Application name for identification
- `business_criticality` - For risk assessment and prioritization
- `tcp_port`, `udp_port` - Network service identification
- `environment` - Environment classification (Prod/Test/Dev)
- `owned_by`, `managed_by` - Ownership and responsibility
- `data_classification` - Security and compliance requirements

**Sample Query**:
```
Table: cmdb_ci_appl
Fields: sys_id,name,short_description,business_criticality,operational_status,environment,tcp_port,owned_by,managed_by,data_classification,disaster_recovery_tier
Filter: operational_status!=Retired
```

### 2. Servers (cmdb_ci_server, cmdb_ci_computer)
**Purpose**: Infrastructure mapping and server-to-application relationships

**Critical Fields**:
- `sys_id` - Primary key for relationships
- `name`, `fqdn` - Server identification
- `ip_address` - Network topology mapping
- `os`, `os_version` - Platform information
- `cpu_count`, `memory`, `disk_space` - Capacity planning
- `environment` - Environment classification
- `virtual` - Physical vs virtual identification

**Sample Query**:
```
Table: cmdb_ci_server
Fields: sys_id,name,fqdn,ip_address,os,os_version,cpu_count,memory,disk_space,environment,virtual,operational_status,owned_by,managed_by,location
Filter: operational_status=Operational
```

### 3. Databases (cmdb_ci_database)
**Purpose**: Database discovery and ERD generation

**Critical Fields**:
- `sys_id` - Primary key
- `database_name`, `instance_name` - Database identification
- `vendor`, `version` - Database platform
- `tcp_port` - Network service mapping
- `installed_on`, `runs_on` - Server relationships
- `data_classification` - Security requirements

### 4. Relationships (cmdb_rel_ci)
**Purpose**: Component dependency mapping and network topology

**Critical Fields**:
- `parent`, `child` - CI relationship mapping
- `type` - Relationship type classification
- `port` - Network port for connections

### 5. Load Balancers (cmdb_ci_load_balancer, cmdb_ci_lb_bigip, cmdb_ci_aws_elb)
**Purpose**: Network infrastructure visualization

**Critical Fields**:
- `dns_name`, `ip_address` - Network identification
- `virtual_servers`, `pools` - Load balancing configuration
- `listeners`, `target_groups` - AWS ALB specific

## Data Quality Requirements

### Mandatory Fields
Fields that MUST be populated for the framework to function:
- All `sys_id` fields
- `name` fields for all CIs
- `ip_address` for servers and network components
- `parent`/`child` in relationships table

### Optional but Recommended
Fields that enhance functionality:
- `business_criticality` - Enables risk-based visualization
- `environment` - Supports environment-specific views
- `data_classification` - Required for compliance reporting

## Export Configuration

### Export Parameters
```json
{
  "format": "JSON",
  "encoding": "UTF-8",
  "date_format": "ISO 8601",
  "include_display_values": true,
  "include_reference_links": true,
  "max_records_per_table": 50000,
  "exclude_retired_cis": true
}
```

### Filters to Apply
- `operational_status != 'Retired'`
- `install_status = 'Installed'` (for applications)
- Only active relationships
- Include all environments (Production, Test, Development)

## Validation Checklist

Before processing the export, validate:

✅ **Data Completeness**
- [ ] All required tables are present
- [ ] Critical fields are populated (>90% completion rate)
- [ ] sys_id fields are unique and not null

✅ **Relationship Integrity**
- [ ] Parent/child relationships reference valid sys_ids
- [ ] Application-to-server relationships exist
- [ ] IP addresses match between servers and IP address table

✅ **Data Quality**
- [ ] IP addresses are valid format
- [ ] Ports are numeric values
- [ ] Environment values are standardized
- [ ] No duplicate names within same CI type

## Troubleshooting Common Issues

### Missing Relationships
**Problem**: Applications not showing server dependencies
**Solution**: Verify cmdb_rel_ci table includes "Runs on" relationships

### Incomplete Network Topology
**Problem**: Load balancers not connecting to servers
**Solution**: Ensure load balancer target groups/pools reference correct server names

### Database ERD Issues
**Problem**: Database tables not showing relationships
**Solution**: Requires additional database discovery tools for schema-level metadata

## Security and Compliance Notes

### Data Masking Requirements
- Mask connection strings containing passwords
- Remove sensitive environment variables
- Redact personal identifiable information (PII)

### Access Controls
- Limit export to authorized personnel
- Implement audit logging for data exports
- Follow data governance policies for external tool usage

## Contact Information
For questions about ServiceNow field requirements:
- CMDB Team: cmdb.team@company.com
- Architecture Team: architecture@company.com
- Data Governance: governance@company.com

## Usage Instructions

1. **Generate Templates**: Run the script to create Excel and JSON templates
2. **Export Data**: Use ServiceNow's export functionality with the provided field lists
3. **Validate Data**: Use the validation checklist before processing
4. **Import to Framework**: Use the generated files as input to your metadata discovery tools

## Additional ServiceNow Tables

### Optional Tables for Enhanced Discovery
- `cmdb_ci_service` - Business services
- `cmdb_ci_network_gear` - Network equipment
- `cmdb_ci_storage_server` - Storage systems
- `cmdb_ci_cluster` - Virtualization clusters
- `cmdb_ci_app_server` - Application servers

### Cloud Resources
- `cmdb_ci_cloud_service_account` - Cloud accounts
- `cmdb_ci_vm_instance` - Virtual machines
- `cmdb_ci_kubernetes_cluster` - K8s clusters
- `cmdb_ci_container` - Container instances
