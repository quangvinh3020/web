async function fetchUsers() {
    try{
        const response = await fetch("https://jsonplaceholder.typicode.com/users");
        const users = await response.json();
        const userList = document.getElementById("userList");
        users.forEach(user=>{
            const li = document.createElement("li");
            li.innerText = user.name;
            userList.appendChild(li);
        });
    }catch(error){
        console.error("Error fetching users:", error);
    }
}
fetchUsers();