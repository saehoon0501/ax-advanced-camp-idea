#!/usr/bin/env node

/**
 * Simple Hello World printer in Node.js
 */

console.log('Hello, World!');

// Optional: Add some additional functionality
function printHello(name = 'World') {
    console.log(`Hello, ${name}!`);
}

// If command line arguments are provided, use them
if (process.argv.length > 2) {
    const name = process.argv.slice(2).join(' ');
    printHello(name);
} else {
    printHello();
}