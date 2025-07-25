const orders = [
    {name: "HTML Course", price: 3000000},
    {name: "JS Course", price: 250000},
    {name: "React Course", price: 320000}
];

function getTotal(orders){
    return orders.reduce((sum, order)=>sum + order.price, 0);
}
console.log(getTotal(orders));