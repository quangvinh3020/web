function divide(a, b){
    try{
        if (b === 0) throw new Error("Division by zero");
        return a/b;
    }catch (error){
        console.error(error.message);
        return null;
    }
}

console.log(divide(10, 2));
console.log(divide(10, 0));