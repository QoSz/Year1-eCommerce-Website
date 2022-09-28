// Reference Material: (JavaScript : Credit Card Number validation - w3resource. 2020)

function cardnumber(inputtxt)
{
  var cardno = /^(?:5[1-5][0-9]{14})$/;
  if(inputtxt.value.match(cardno))
        {
      return true;
        }
      else
        {
        alert("Not a valid Mastercard number!");
        return false;
        }
}


// Reference List
// JavaScript : Credit Card Number validation - w3resource. 2020. Available at: https://www.w3resource.com/javascript/form/credit-card-validation.php [Accessed: 14 May 2021].