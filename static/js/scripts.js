alert("Working test");

// Add Patient pop Up JS

document.addEventListener("DOMContentLoaded", function () {




  const modal = document.getElementById("patientModal");
  const btn = document.getElementById("openPatientModal");
  const closeBtn = document.querySelector(".close-modal");
  const cancelBtn = document.querySelector(".btn-cancel");

  //   Open the modal
  btn.onclick = function (e) {
    e.preventDefault(); // Stop form submission
    modal.style.display = "block";
  };

  //   Close the modal (clicking X or Cancel)
  const closeModal = () => (modal.style.display = "none");

  closeBtn.onclick = closeModal;
  cancelBtn.onclick = closeModal;

  // Close if user clicks outside the white box
  window.onclick = function (event) {
    if (event.target == modal) {
      closeModal();
    }
  };



 





});
