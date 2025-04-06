// API utility functions

/**
 * Make a GET request to the API
 *
 * @param {string} url - The URL to fetch
 * @returns {Promise} - The response data
 */
async function apiGet(url) {
  try {
    const response = await fetch(url)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error("API GET Error:", error)
    throw error
  }
}

/**
 * Make a POST request to the API
 *
 * @param {string} url - The URL to fetch
 * @param {Object} data - The data to send
 * @returns {Promise} - The response data
 */
async function apiPost(url, data) {
  try {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content")

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error("API POST Error:", error)
    throw error
  }
}

/**
 * Make a PUT request to the API
 *
 * @param {string} url - The URL to fetch
 * @param {Object} data - The data to send
 * @returns {Promise} - The response data
 */
async function apiPut(url, data) {
  try {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content")

    const response = await fetch(url, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error("API PUT Error:", error)
    throw error
  }
}

/**
 * Make a DELETE request to the API
 *
 * @param {string} url - The URL to fetch
 * @returns {Promise} - The response data
 */
async function apiDelete(url) {
  try {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content")

    const response = await fetch(url, {
      method: "DELETE",
      headers: {
        "X-CSRFToken": csrfToken,
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error("API DELETE Error:", error)
    throw error
  }
}

/**
 * Upload a file to the API
 *
 * @param {string} url - The URL to fetch
 * @param {FormData} formData - The form data with file
 * @returns {Promise} - The response data
 */
async function apiUploadFile(url, formData) {
  try {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content")

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
      },
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error("API Upload Error:", error)
    throw error
  }
}

/**
 * Make an AI analysis request
 *
 * @param {string} text - The text to analyze
 * @param {number} blockId - The block ID
 * @param {string} provider - The AI provider
 * @returns {Promise} - The response data
 */
async function apiAnalyzeText(text, blockId, provider = "yandex") {
  return apiPost("/ai/analyze", {
    text: text,
    block_id: blockId,
    provider: provider,
  })
}

/**
 * Update recommendation status
 *
 * @param {number} recommendationId - The recommendation ID
 * @param {string} status - The new status
 * @returns {Promise} - The response data
 */
async function apiUpdateRecommendation(recommendationId, status) {
  return apiPut(`/recommendations/${recommendationId}`, {
    status: status,
  })
}

/**
 * Report an error
 *
 * @param {FormData} formData - The form data with error details
 * @returns {Promise} - The response data
 */
async function apiReportError(formData) {
  return apiUploadFile("/report-error", formData)
}

