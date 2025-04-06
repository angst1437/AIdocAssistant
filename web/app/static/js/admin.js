document.addEventListener("DOMContentLoaded", () => {
  // Admin users page
  if (window.location.pathname.includes("/admin/users")) {
    initUserManagement()
  }

  // Admin error reports page
  if (window.location.pathname.includes("/admin/error-reports")) {
    initErrorReports()
  }

  // Admin logs page
  if (window.location.pathname.includes("/admin/logs")) {
    initLogs()
  }
})

// Initialize user management
function initUserManagement() {
  const toggleButtons = document.querySelectorAll(".toggle-user-active-btn")

  toggleButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const userId = this.getAttribute("data-user-id")

      fetch(`/admin/users/${userId}/toggle-active`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            // Reload the page to reflect changes
            window.location.reload()
          } else {
            alert(data.error || "Произошла ошибка")
          }
        })
        .catch((error) => {
          console.error("Error:", error)
          alert("Произошла ошибка при выполнении запроса")
        })
    })
  })
}

// Initialize error reports
function initErrorReports() {
  const viewButtons = document.querySelectorAll(".view-report-btn")
  const reportModal = document.getElementById("report-detail-modal")
  const closeReportModal = document.getElementById("close-report-modal")
  const statusForms = document.querySelectorAll(".status-update-form")

  viewButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const reportId = this.getAttribute("data-report-id")
      const row = this.closest("tr")

      // Fill modal with data from the row
      document.getElementById("report-id").textContent = row.cells[0].textContent.trim()
      document.getElementById("report-user").textContent = row.cells[1].querySelector(".text-sm").textContent.trim()
      document.getElementById("report-description").textContent = row.cells[2]
        .querySelector(".text-sm")
        .textContent.trim()
      document.getElementById("report-date").textContent = row.cells[3].textContent.trim()
      document.getElementById("report-status").textContent = row.cells[4].querySelector("span").textContent.trim()

      // Check if there's a screenshot
      const screenshotContainer = document.getElementById("screenshot-container")
      const reportScreenshot = document.getElementById("report-screenshot")

      // Fetch the report details to get the screenshot URL
      fetch(`/admin/error-reports/${reportId}/details`, {
        headers: {
          "X-CSRFToken": getCsrfToken(),
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.screenshot_url) {
            reportScreenshot.src = data.screenshot_url
            screenshotContainer.classList.remove("hidden")
          } else {
            screenshotContainer.classList.add("hidden")
          }
        })
        .catch((error) => {
          console.error("Error fetching report details:", error)
          screenshotContainer.classList.add("hidden")
        })

      reportModal.classList.remove("hidden")
    })
  })

  if (closeReportModal) {
    closeReportModal.addEventListener("click", () => {
      reportModal.classList.add("hidden")
    })
  }

  statusForms.forEach((form) => {
    form.addEventListener("submit", function (e) {
      e.preventDefault()

      const formData = new FormData(this)

      fetch(this.action, {
        method: "POST",
        body: formData,
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            // Reload the page to reflect changes
            window.location.reload()
          } else {
            alert(data.error || "Произошла ошибка")
          }
        })
        .catch((error) => {
          console.error("Error:", error)
          alert("Произошла ошибка при выполнении запроса")
        })
    })
  })
}

// Initialize logs
function initLogs() {
  // Add any specific functionality for the logs page here
}

// Get CSRF token
function getCsrfToken() {
  return document.querySelector('meta[name="csrf-token"]').getAttribute("content")
}

