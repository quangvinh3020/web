const taskInput = document.getElementById("taskInput");
const addBtn = document.getElementById("addBtn");
const taskList = document.getElementById("taskList");

addBtn.addEventListener("click", ()=>{
    const taskText = taskInput.value.trim();
    if (taskText){
        const li = document.createElement("li");
        li.className = "todo-item";
        li.draggable = true;
        li.innerHTML = `${taskText} <span class="delete-btn>Delete</span>`;
        
        taskList.appendChild(li);
        taskInput.value ="";

        li.querySelector(".delete-btn").addEventListener("click", ()=>{
            li.remove();
        });

        li.addEventListener("dragstart", ()=>{
            li.classList.add("dragging");
        });

        li.addEventListener("dragend", ()=>{
            li.classList.remove("dragging");
        });

        li.addEventListener("dragover", (e)=>{
            e.preventDefault();
        });

        li.addEventListener("drop", (e)=>{
            e.preventDefault();
            const dragging = document.querySelector(".dragging");
            taskList.insertBefore(dragging, li);
        });
    }
});