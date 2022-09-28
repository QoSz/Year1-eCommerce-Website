// Reference Material: (Garg 2018)

function validate() {
    var pass = document.getElementById("newpassword").value;
    var cpass = document.getElementById("cpassword").value;
    if (pass == cpass) {
        return true;
    } else {
        alert("Passwords do not match!");
        return false;
    }
}


// References
// Garg, N. 2018. Password Matching using JavaScript - GeeksforGeeks. Available at: https://www.geeksforgeeks.org/password-matching-using-javascript/ [Accessed: 14 May 2021].

