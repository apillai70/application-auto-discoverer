// Example JavaScript for debugging
console.log("🟨 JavaScript Debug Example");

function calculateFactorial(n) {
    if (n <= 1) return 1;
    return n * calculateFactorial(n - 1);
}

function main() {
    console.log("Calculating factorials...");
    
    for (let i = 1; i <= 10; i++) {
        const result = calculateFactorial(i);
        console.log(`${i}! = ${result}`);
    }
    
    console.log("✅ JavaScript example completed!");
}

main();
