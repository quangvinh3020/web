const questions = [
    {
        question: "What is the capital of France?",
        options: ["Berlin", "Madrid", "Paris", "Rome"],
        answer: "Paris"
    },
    {
        question: "Which planet is known as the Red Planet?",
        options: ["Earth", "Mars", "Jupiter", "Venus"],
        answer: "Mars"
    },
    {
        question: "What is the largest ocean on Earth?",
        options: ["Atlantic Ocean", "Indian Ocean", "Arctic Ocean", "Pacific Ocean"],
        answer: "Pacific Ocean"
    },
    {
        question: "What is the chemical symbol for water?",
        options: ["O2", "H2O", "CO2", "N2"],
        answer: "H2O"
    },
    {
        question: "Who painted the Mona Lisa?",
        options: ["Vincent van Gogh", "Pablo Picasso", "Leonardo da Vinci", "Claude Monet"],
        answer: "Leonardo da Vinci"
    }
];

const questionDisplay = document.getElementById('question-display');
const optionsContainer = document.getElementById('options-container');
const submitBtn = document.getElementById('submit-btn');
const resultDisplay = document.getElementById('result-display');
const restartBtn = document.getElementById('restart-btn');

let currentQuestionIndex = 0;
let score = 0;

function loadQuestion() {
    const currentQuestion = questions[currentQuestionIndex];
    questionDisplay.textContent = currentQuestion.question; 

    optionsContainer.innerHTML = ''; 
    currentQuestion.options.forEach((option, index) => {
        const optionItem = document.createElement('div');
        optionItem.classList.add('option-item');
        optionItem.innerHTML = `
            <input type="radio" id="option${index}" name="answer" value="${option}">
            <label for="option${index}">${option}</label>
        `;
        optionsContainer.appendChild(optionItem); 
    });

    submitBtn.style.display = 'block'; 
    resultDisplay.textContent = ''; 
    restartBtn.style.display = 'none'; 
}


function checkAnswer() {
    const selectedOption = document.querySelector('input[name="answer"]:checked');
    if (!selectedOption) {
        resultDisplay.textContent = "Please select an answer!";
        return;
    }

    const userAnswer = selectedOption.value;
    const correctAnswer = questions[currentQuestionIndex].answer;

    if (userAnswer === correctAnswer) {
        score++; 
        resultDisplay.textContent = "Correct!";
        resultDisplay.style.color = 'green';
    } else {
        resultDisplay.textContent = `Incorrect! The correct answer was: ${correctAnswer}`;
        resultDisplay.style.color = 'red';
    }

    submitBtn.style.display = 'none'; 
    setTimeout(() => {
        currentQuestionIndex++;
        if (currentQuestionIndex < questions.length) {
            loadQuestion(); 
        } else {
            showFinalScore(); 
        }
    }, 1500); 
}

function showFinalScore() {
    questionDisplay.textContent = "Quiz Completed!";
    optionsContainer.innerHTML = '';
    resultDisplay.textContent = `Your final score is: ${score} out of ${questions.length}`;
    resultDisplay.style.color = '#333';
    submitBtn.style.display = 'none'; 
    restartBtn.style.display = 'block'; 
}

function restartQuiz() {
    currentQuestionIndex = 0;
    score = 0;
    loadQuestion();
}

submitBtn.addEventListener('click', checkAnswer);
restartBtn.addEventListener('click', restartQuiz);

loadQuestion();