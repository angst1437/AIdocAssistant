document.addEventListener("DOMContentLoaded", () => {
  // Global variables
  const editors = {}
  let currentBlockId = null
  let currentAiProvider = "yandex"

  // Declare ClassicEditor and showToast (assuming they are globally available or defined elsewhere)
  let ClassicEditor
  let showToast

  // Initialize CKEditor for each block
  function initializeEditors() {
    document.querySelectorAll(".editor").forEach((editorElement) => {
      const blockId = editorElement.getAttribute("data-block-id")

      ClassicEditor = window.ClassicEditor // Access ClassicEditor from the window object

      ClassicEditor.create(editorElement, {
        toolbar: [
          "heading",
          "|",
          "bold",
          "italic",
          "link",
          "bulletedList",
          "numberedList",
          "|",
          "outdent",
          "indent",
          "|",
          "blockQuote",
          "insertTable",
          "undo",
          "redo",
        ],
        placeholder: "Введите текст...",
        heading: {
          options: [
            { model: "paragraph", view: "p", title: "Абзац", class: "ck-heading_paragraph" },
            { model: "heading1", view: "h1", title: "Заг��ловок 1", class: "ck-heading_heading1" },
            { model: "heading2", view: "h2", title: "Заголовок 2", class: "ck-heading_heading2" },
            { model: "heading3", view: "h3", title: "Заголовок 3", class: "ck-heading_heading3" },
          ],
        },
      })
        .then((editor) => {
          editors[blockId] = editor

          // Set focus on the editor when clicked
          editor.ui.focusTracker.on("change:isFocused", (evt, name, isFocused) => {
            if (isFocused) {
              currentBlockId = blockId
            }
          })

          // Auto-save content when editor loses focus
          editor.ui.focusTracker.on("change:isFocused", (evt, name, isFocused) => {
            if (!isFocused) {
              saveBlockContent(blockId)
            }
          })
        })
        .catch((error) => {
          console.error("Error initializing editor:", error)
        })
    })
  }

  // Save block content
  function saveBlockContent(blockId) {
    if (!editors[blockId]) return

    const content = editors[blockId].getData()
    const blockTypeSelect = document.querySelector(`.editor-block[data-block-id="${blockId}"] .block-type-select`)
    const blockType = blockTypeSelect ? blockTypeSelect.value : "paragraph"

    fetch(`/blocks/${blockId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({
        content: content,
        block_type: blockType,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (!data.success) {
          showToast("Ошибка при сохранении блока", "error")
        }
      })
      .catch((error) => {
        console.error("Error saving block:", error)
        showToast("Ошибка при сохранении блока", "error")
      })
  }

  // Add new block
  function addNewBlock() {
    const documentId = window.location.pathname.split("/")[1]

    fetch(`/documents/${documentId}/blocks`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({
        content: "",
        block_type: "paragraph",
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        // Create new block HTML
        const editorContainer = document.getElementById("editor-container")
        const newBlockHtml = `
                <div class="editor-block mb-4" data-block-id="${data.id}">
                    <div class="editor-toolbar flex justify-between items-center mb-2">
                        <select class="block-type-select border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
                            <option value="paragraph" selected>Абзац</option>
                            <option value="heading">Заголовок</option>
                            <option value="list">Список</option>
                        </select>
                        <div class="flex space-x-2">
                            <button class="analyze-block-btn px-3 py-1 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                Проверить
                            </button>
                            <button class="delete-block-btn px-3 py-1 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                Удалить
                            </button>
                        </div>
                    </div>
                    <div class="editor" data-block-id="${data.id}"></div>
                </div>
            `

        editorContainer.insertAdjacentHTML("beforeend", newBlockHtml)

        // Initialize the new editor
        const newEditorElement = document.querySelector(`.editor[data-block-id="${data.id}"]`)

        ClassicEditor = window.ClassicEditor // Access ClassicEditor from the window object

        ClassicEditor.create(newEditorElement, {
          toolbar: [
            "heading",
            "|",
            "bold",
            "italic",
            "link",
            "bulletedList",
            "numberedList",
            "|",
            "outdent",
            "indent",
            "|",
            "blockQuote",
            "insertTable",
            "undo",
            "redo",
          ],
          placeholder: "Введите текст...",
          heading: {
            options: [
              { model: "paragraph", view: "p", title: "Абзац", class: "ck-heading_paragraph" },
              { model: "heading1", view: "h1", title: "Заголовок 1", class: "ck-heading_heading1" },
              { model: "heading2", view: "h2", title: "Заголовок 2", class: "ck-heading_heading2" },
              { model: "heading3", view: "h3", title: "Заголовок 3", class: "ck-heading_heading3" },
            ],
          },
        })
          .then((editor) => {
            editors[data.id] = editor
            currentBlockId = data.id

            // Set focus on the new editor
            editor.focus()

            // Auto-save content when editor loses focus
            editor.ui.focusTracker.on("change:isFocused", (evt, name, isFocused) => {
              if (!isFocused) {
                saveBlockContent(data.id)
              }
            })

            // Set focus on the editor when clicked
            editor.ui.focusTracker.on("change:isFocused", (evt, name, isFocused) => {
              if (isFocused) {
                currentBlockId = data.id
              }
            })
          })
          .catch((error) => {
            console.error("Error initializing new editor:", error)
          })

        // Add event listeners for the new block
        addBlockEventListeners()
      })
      .catch((error) => {
        console.error("Error adding block:", error)
        showToast("Ошибка при добавлении блока", "error")
      })
  }

  // Delete block
  function deleteBlock(blockId) {
    if (confirm("Вы уверены, что хотите удалить этот блок?")) {
      fetch(`/blocks/${blockId}`, {
        method: "DELETE",
        headers: {
          "X-CSRFToken": getCsrfToken(),
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            // Remove the block from the DOM
            const blockElement = document.querySelector(`.editor-block[data-block-id="${blockId}"]`)
            if (blockElement) {
              blockElement.remove()
            }

            // Destroy the editor instance
            if (editors[blockId]) {
              editors[blockId].destroy().then(() => {
                delete editors[blockId]
              })
            }

            showToast("Блок успешно удален")
          } else {
            showToast("Ошибка при удалении блока", "error")
          }
        })
        .catch((error) => {
          console.error("Error deleting block:", error)
          showToast("Ошибка при удалении блока", "error")
        })
    }
  }

  // Analyze block with AI
  function analyzeBlock(blockId) {
    if (!editors[blockId]) return

    const content = editors[blockId].getData()
    if (!content.trim()) {
      showToast("Блок пуст. Нечего анализировать.", "error")
      return
    }

    // Show loading state
    const analyzeBtn = document.querySelector(`.editor-block[data-block-id="${blockId}"] .analyze-block-btn`)
    if (analyzeBtn) {
      const originalText = analyzeBtn.textContent
      analyzeBtn.textContent = "Анализ..."
      analyzeBtn.disabled = true

      // Clear previous recommendations
      document.getElementById("recommendations-container").innerHTML = `
                <div class="text-center py-4">
                    <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-indigo-500 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <p class="mt-2 text-sm text-gray-500">Анализ текста...</p>
                </div>
            `

      // Send request to analyze
      fetch("/ai/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({
          text: content,
          block_id: blockId,
          provider: currentAiProvider,
        }),
      })
        .then((response) => response.json())
        .then((recommendations) => {
          // Reset button state
          analyzeBtn.textContent = originalText
          analyzeBtn.disabled = false

          // Display recommendations
          displayRecommendations(recommendations, blockId)
        })
        .catch((error) => {
          console.error("Error analyzing block:", error)
          showToast("Ошибка при анализе блока", "error")

          // Reset button state
          analyzeBtn.textContent = originalText
          analyzeBtn.disabled = false

          // Show error message in recommendations container
          document.getElementById("recommendations-container").innerHTML = `
                    <div class="text-center text-red-500 py-4">
                        <p>Произошла ошибка при анализе текста.</p>
                    </div>
                `
        })
    }
  }

  // Display recommendations
  function displayRecommendations(recommendations, blockId) {
    const container = document.getElementById("recommendations-container")

    if (!recommendations || recommendations.length === 0) {
      container.innerHTML = `
                <div class="text-center text-green-500 py-8">
                    <svg class="mx-auto h-12 w-12" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                    <p class="mt-2">Ошибок не найдено. Текст соответствует требованиям.</p>
                </div>
            `
      return
    }

    let html = ""

    recommendations.forEach((rec) => {
      const typeClass = getRecommendationTypeClass(rec.type_of_error)

      html += `
                <div class="recommendation p-4 rounded-lg border border-gray-200 hover:border-indigo-200" 
                     data-recommendation-id="${rec.id}" 
                     data-block-id="${blockId}"
                     data-start="${rec.start_char}"
                     data-end="${rec.end_char}">
                    <div class="flex justify-between items-start">
                        <span class="recommendation-type ${typeClass}">
                            ${getRecommendationTypeLabel(rec.type_of_error)}
                        </span>
                        <div class="flex space-x-2">
                            <button class="accept-recommendation-btn text-xs px-2 py-1 bg-green-50 text-green-700 rounded hover:bg-green-100">
                                Принять
                            </button>
                            <button class="reject-recommendation-btn text-xs px-2 py-1 bg-red-50 text-red-700 rounded hover:bg-red-100">
                                Отклонить
                            </button>
                        </div>
                    </div>
                    <div class="mt-2">
                        <p class="text-sm font-medium text-gray-900">Проблема:</p>
                        <p class="text-sm text-gray-700 mt-1">${rec.original_text}</p>
                    </div>
                    <div class="mt-2">
                        <p class="text-sm font-medium text-gray-900">Рекомендация:</p>
                        <p class="text-sm text-gray-700 mt-1">${rec.suggestion}</p>
                    </div>
                    <div class="mt-2">
                        <p class="text-sm font-medium text-gray-900">Объяснение:</p>
                        <p class="text-sm text-gray-700 mt-1">${rec.explanation}</p>
                    </div>
                </div>
            `
    })

    container.innerHTML = html

    // Add event listeners for recommendations
    addRecommendationEventListeners()
  }

  // Get recommendation type class
  function getRecommendationTypeClass(type) {
    switch (type.toLowerCase()) {
      case "style":
        return "recommendation-type-style"
      case "grammar":
        return "recommendation-type-grammar"
      case "gost":
        return "recommendation-type-gost"
      case "terminology":
        return "recommendation-type-terminology"
      case "logic":
        return "recommendation-type-logic"
      default:
        return "recommendation-type-style"
    }
  }

  // Get recommendation type label
  function getRecommendationTypeLabel(type) {
    switch (type.toLowerCase()) {
      case "style":
        return "Стиль"
      case "grammar":
        return "Грамматика"
      case "gost":
        return "ГОСТ"
      case "terminology":
        return "Терминология"
      case "logic":
        return "Логика"
      default:
        return type
    }
  }

  // Add event listeners for recommendations
  function addRecommendationEventListeners() {
    // Highlight text when recommendation is clicked
    document.querySelectorAll(".recommendation").forEach((rec) => {
      rec.addEventListener("click", function () {
        const blockId = this.getAttribute("data-block-id")
        const start = Number.parseInt(this.getAttribute("data-start"))
        const end = Number.parseInt(this.getAttribute("data-end"))

        if (editors[blockId]) {
          // Remove active class from all recommendations
          document.querySelectorAll(".recommendation").forEach((r) => {
            r.classList.remove("active")
          })

          // Add active class to clicked recommendation
          this.classList.add("active")

          // Highlight text in editor
          highlightTextInEditor(blockId, start, end)
        }
      })
    })

    // Accept recommendation
    document.querySelectorAll(".accept-recommendation-btn").forEach((btn) => {
      btn.addEventListener("click", function (e) {
        e.stopPropagation()

        const recElement = this.closest(".recommendation")
        const recId = recElement.getAttribute("data-recommendation-id")
        const blockId = recElement.getAttribute("data-block-id")
        const start = Number.parseInt(recElement.getAttribute("data-start"))
        const end = Number.parseInt(recElement.getAttribute("data-end"))

        // Get the recommendation data
        const suggestion = recElement.querySelector("p:nth-of-type(4)").textContent

        // Apply the suggestion to the editor
        if (editors[blockId]) {
          const editor = editors[blockId]
          const editorContent = editor.getData()

          // Create a temporary div to parse the HTML content
          const tempDiv = document.createElement("div")
          tempDiv.innerHTML = editorContent

          // Extract text content
          const textContent = tempDiv.textContent

          // Check if the start and end positions are valid
          if (start >= 0 && end <= textContent.length) {
            // Replace the text in the editor
            // This is a simplified approach and might not work perfectly with complex HTML
            // A more robust solution would use the CKEditor API for text replacement
            const beforeText = editorContent.substring(0, start)
            const afterText = editorContent.substring(end)

            editor.setData(beforeText + suggestion + afterText)

            // Save the block content
            saveBlockContent(blockId)

            // Update recommendation status
            updateRecommendationStatus(recId, "accepted")

            // Remove the recommendation from the list
            recElement.remove()

            showToast("Рекомендация принята")
          } else {
            showToast("Не удалось применить рекомендацию", "error")
          }
        }
      })
    })

    // Reject recommendation
    document.querySelectorAll(".reject-recommendation-btn").forEach((btn) => {
      btn.addEventListener("click", function (e) {
        e.stopPropagation()

        const recElement = this.closest(".recommendation")
        const recId = recElement.getAttribute("data-recommendation-id")

        // Update recommendation status
        updateRecommendationStatus(recId, "rejected")

        // Remove the recommendation from the list
        recElement.remove()

        showToast("Рекомендация отклонена")
      })
    })
  }

  // Highlight text in editor
  function highlightTextInEditor(blockId, start, end) {
    if (!editors[blockId]) return

    const editor = editors[blockId]

    // Focus the editor
    editor.focus()

    // This is a simplified approach and might not work perfectly with complex HTML
    // A more robust solution would use the CKEditor API for selection
    const editorContent = editor.getData()

    // Create a temporary div to parse the HTML content
    const tempDiv = document.createElement("div")
    tempDiv.innerHTML = editorContent

    // Extract text content
    const textContent = tempDiv.textContent

    // Check if the start and end positions are valid
    if (start >= 0 && end <= textContent.length) {
      // Scroll to the position in the editor
      // This is a simplified approach and might not work perfectly
      const selection = editor.model.document.selection
      const position = editor.model.createPositionAt(editor.model.document.getRoot(), start)

      editor.model.change((writer) => {
        writer.setSelection(position)
      })
    }
  }

  // Update recommendation status
  function updateRecommendationStatus(recId, status) {
    fetch(`/recommendations/${recId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({
        status: status,
      }),
    })
      .then((response) => response.json())
      .catch((error) => {
        console.error("Error updating recommendation status:", error)
      })
  }

  // Add event listeners for blocks
  function addBlockEventListeners() {
    // Block type select
    document.querySelectorAll(".block-type-select").forEach((select) => {
      select.addEventListener("change", function () {
        const blockId = this.closest(".editor-block").getAttribute("data-block-id")
        saveBlockContent(blockId)
      })
    })

    // Analyze block button
    document.querySelectorAll(".analyze-block-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        const blockId = this.closest(".editor-block").getAttribute("data-block-id")
        analyzeBlock(blockId)
      })
    })

    // Delete block button
    document.querySelectorAll(".delete-block-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        const blockId = this.closest(".editor-block").getAttribute("data-block-id")
        deleteBlock(blockId)
      })
    })
  }

  // Save document title
  function saveDocumentTitle() {
    const titleInput = document.getElementById("document-title")
    if (!titleInput) return

    const documentId = window.location.pathname.split("/")[1]

    fetch(`/${documentId}/update`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({
        title: titleInput.value,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showToast("Название документа сохранено")
        } else {
          showToast("Ошибка при сохранении названия документа", "error")
        }
      })
      .catch((error) => {
        console.error("Error saving document title:", error)
        showToast("Ошибка при сохранении названия документа", "error")
      })
  }

  // Get CSRF token
  function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute("content")
  }

  // Initialize the editor
  initializeEditors()

  // Add event listeners
  addBlockEventListeners()

  // Add block button
  const addBlockBtn = document.getElementById("add-block-btn")
  if (addBlockBtn) {
    addBlockBtn.addEventListener("click", addNewBlock)
  }

  // Save document button
  const saveDocumentBtn = document.getElementById("save-document")
  if (saveDocumentBtn) {
    saveDocumentBtn.addEventListener("click", () => {
      // Save the current block if any
      if (currentBlockId) {
        saveBlockContent(currentBlockId)
      }

      // Save the document title
      saveDocumentTitle()
    })
  }

  // Document title input
  const documentTitleInput = document.getElementById("document-title")
  if (documentTitleInput) {
    documentTitleInput.addEventListener("blur", saveDocumentTitle)
  }

  // AI provider selection
  document.querySelectorAll(".ai-provider-option").forEach((option) => {
    option.addEventListener("click", function (e) {
      e.preventDefault()

      const provider = this.getAttribute("data-provider")
      currentAiProvider = provider

      // Update the button text
      const providerButton = this.closest(".relative").querySelector("button span")
      if (providerButton) {
        providerButton.textContent = this.textContent
      }

      showToast(`ИИ-провайдер изменен на ${this.textContent}`)
    })
  })
})

