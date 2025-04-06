document.addEventListener("DOMContentLoaded", () => {
  // Error modal functionality
  const errorModal = document.getElementById("error-modal")
  const openErrorModalBtn = document.getElementById("open-error-modal")
  const closeErrorModalBtn = document.getElementById("close-error-modal")
  const submitErrorReportBtn = document.getElementById("submit-error-report")
  const errorReportForm = document.getElementById("error-report-form")

  // Add "Report Error" button to the header if it doesn't exist
  if (!openErrorModalBtn) {
    const headerNav = document.querySelector("header nav")
    if (headerNav) {
      const reportErrorBtn = document.createElement("a")
      reportErrorBtn.href = "#"
      reportErrorBtn.id = "open-error-modal"
      reportErrorBtn.className =
        "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
      reportErrorBtn.textContent = "Сообщить об ошибке"
      headerNav.appendChild(reportErrorBtn)
    }
  }

  // Initialize error modal functionality
  document.addEventListener("click", (e) => {
    if (e.target && e.target.id === "open-error-modal") {
      e.preventDefault()
      errorModal.classList.remove("hidden")
    }
  })

  if (closeErrorModalBtn) {
    closeErrorModalBtn.addEventListener("click", () => {
      errorModal.classList.add("hidden")
    })
  }

  // Toast notification functionality
  window.showToast = (message, type = "success") => {
    const toast = document.createElement("div")
    toast.className = "toast"

    const icon =
      type === "success"
        ? '<svg class="h-5 w-5 text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" /></svg>'
        : '<svg class="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" /></svg>'

    toast.innerHTML = `
            <div class="flex items-center">
                <div class="flex-shrink-0">
                    ${icon}
                </div>
                <div class="ml-3">
                    <p class="text-sm font-medium text-gray-900">${message}</p>
                </div>
            </div>
        `

    document.body.appendChild(toast)

    // Show the toast
    setTimeout(() => {
      toast.classList.add("show")
    }, 10)

    // Hide and remove the toast after 3 seconds
    setTimeout(() => {
      toast.classList.remove("show")
      setTimeout(() => {
        document.body.removeChild(toast)
      }, 300)
    }, 3000)
  }

  if (submitErrorReportBtn && errorReportForm) {
    submitErrorReportBtn.addEventListener("click", (e) => {
      e.preventDefault()

      const formData = new FormData(errorReportForm)

      fetch("/report-error", {
        method: "POST",
        body: formData,
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            showToast("Сообщение об ошибке успешно отправлено")
            errorModal.classList.add("hidden")
            errorReportForm.reset()
          } else {
            showToast(data.error || "Произошла ошибка при отправке сообщения", "error")
          }
        })
        .catch((error) => {
          console.error("Error:", error)
          showToast("Произошла ошибка при отправке сообщения", "error")
        })
    })
  }
})

