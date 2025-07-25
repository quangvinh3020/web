const taskInput = document.getElementById("taskInput");
const addBtn = document.getElementById("addBtn");
const taskList = document.getElementById("taskList");

addBtn.addEventListener("click", ()=>{
    const taskText = taskInput.value.trim();
    if (taskText){
        const li = document.createElement("li");
        li.className = "todo-item";
        li.innerHTML = `${taskText} <span class="delete-btn">Delete</span>`;
        taskList.appendChild(li);
        taskInput.value = "";

        li.querySelector(".delete-btn").addEventListener("click", ()=>{
            li.remove();
        });
    }
});