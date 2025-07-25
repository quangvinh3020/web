document.getElementById("submitBtn").addEventListener ("click", ()=> {
 const email = document.getElementById ("email").value ;
 const password = document.getElementById ("password").value ;
 const emailError = document.getElementById ("emailError") ;
 const passwordError = document.getElementById ("passwordError") ;

 emailError.innerText = "";
 passwordError.innerText = "";

 let isValid = true ;

 if (!email) {
 emailError.innerText = "Email is required";
 isValid = false ;
 } else if (!email.includes (" @ ")) {
    emailError.innerText = "Invalid email format";
    isValid = false ;
 }

 if (!password) {
        passwordError.innerText = " Password is required ";
        isValid = false ;
    }  else if ( password.length < 6) {
         passwordError.innerText = " Password must be at least 6 characters ";
        isValid = false ;
    }

 if ( isValid ) {
        console.log (" Form submitted :" , { email , password }) ;
    }
}) ;