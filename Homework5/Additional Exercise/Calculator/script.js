const display = document.getElementById('display'); 
const buttons = document.querySelectorAll('.button'); 

let currentInput = '0'; 
let firstOperand = null; 
let operator = null; 
let waitingForSecondOperand = false; 


function updateDisplay() {
    display.textContent = currentInput;
}


function inputDigit(digit) {
    if (waitingForSecondOperand) {
        currentInput = digit;
        waitingForSecondOperand = false;
    } else {
        currentInput = currentInput === '0' ? digit : currentInput + digit;
    }
    updateDisplay();
}


function inputDecimal(dot) {
    if (waitingForSecondOperand) {
        currentInput = '0.';
        waitingForSecondOperand = false;
        updateDisplay();
        return;
    }
    
    if (!currentInput.includes(dot)) {
        currentInput += dot;
    }
    updateDisplay();
}


function clearCalculator() {
    currentInput = '0';
    firstOperand = null;
    operator = null;
    waitingForSecondOperand = false;
    updateDisplay();
}


function performCalculation() {
    const inputValue = parseFloat(currentInput);

    if (firstOperand === null && !isNaN(inputValue)) {
        firstOperand = inputValue;
    } else if (operator) {
        let result;
        
        switch (operator) {
            case '+':
                result = firstOperand + inputValue;
                break;
            case '-':
                result = firstOperand - inputValue;
                break;
            case '*':
                result = firstOperand * inputValue;
                break;
            case '/':
                if (inputValue === 0) {
                    alert("Cannot divide by zero!"); 
                    clearCalculator();
                    return;
                }
                result = firstOperand / inputValue;
                break;
            default:
                return;
        }
        currentInput = String(result);
        firstOperand = result;
    }
    waitingForSecondOperand = true;
    updateDisplay();
}


function handleOperator(nextOperator) {
    const inputValue = parseFloat(currentInput);

    
    if (operator && waitingForSecondOperand) {
        operator = nextOperator;
        return;
    }

    
    if (firstOperand === null) {
        firstOperand = inputValue;
    } else if (operator) {
        
        performCalculation();
    }

    waitingForSecondOperand = true;
    operator = nextOperator;
}


buttons.forEach(button => {
    button.addEventListener('click', (event) => {
        const { value } = event.target.dataset; 
        const { action } = event.target.dataset; 

        if (value) { 
            inputDigit(value);
        } else if (action) { 
            switch (action) {
                case 'add':
                case 'subtract':
                case 'multiply':
                case 'divide':
                    handleOperator(event.target.textContent); 
                    break;
                case 'clear':
                    clearCalculator();
                    break;
                case 'equals':
                    performCalculation();
                    break;
                case 'decimal': 
                    inputDecimal('.');
                    break;
            }
        }
    });
});


updateDisplay();