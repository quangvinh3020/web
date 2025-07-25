const taskInput = document.getElementById("taskInput");
const addBtn = document.getElementById("addBtn");
const taskList = document.getElementById("taskList");

function loadTasks(){
    const tasks = JSON.parse(localStorage.getItem("tasks") || "[]");
    tasks.forEach(task=>addTask(task));
}

function saveTasks() {
    const tasks = Array.from(taskList.querySelectorAll(".todo-item")).map(
        li=> li.firstChild.textContent.trim()
    );
    localStorage.setItem("tasks", JSON.stringify(tasks));
}

function addTask(taskText) {
    const li = document.createElement("li");
    li.className = "todo-item";
    li.innerHTML = `${taskText} <span class="delete-btn">Delete</span>`;
    taskList.appendChild(li);
    
    li.querySelector(".delete-btn").addEventListener("click", ()=>{
        li.remove();
        saveTasks();
     });
}

addBtn.addEventListener("click", ()=>{
    const taskText = taskInput.value.trim();
    if (taskText){
        addTask(taskText);
        saveTasks();
        taskInput.value ="";
    }
});
loadTasks();