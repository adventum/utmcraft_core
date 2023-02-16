const showSpinner = () => {
    const spinner = document.getElementById('spinner-lock')
    if (!!spinner) {
        spinner.style.visibility = 'visible'
    }
}


const hideSpinner = () => {
    const spinner = document.getElementById('spinner-lock')
    if (!!spinner) {
        spinner.style.visibility = 'hidden'
    }
}


const setIsVisibleByElemsIds = (ids, isVisible) => {
    ids.forEach(element => {
        const elem = document.getElementById(element)
        if (!!elem) {
            elem.hidden = !isVisible
        }
    })
}


const fetchAndSetForm = async (formId) => {
    const formHTML = await fetchFormHTML(formId)
    const formArea = document.getElementById('form-area')
    formArea.innerHTML = formHTML
    initSelect2()
    const formChoices = document.getElementsByClassName('form-selector-choice')
    for (let formChoice of formChoices) {
        const formChoiceFormId = formChoice.getAttribute('formId')
        if (formChoiceFormId !== formId) {
            formChoice.classList.remove('disabled')
        } else {
            formChoice.classList.add('disabled')
        }
    }
    initTooltips()
    initCustomValuesFields()
    initSelectDependencies()
    setIsVisibleByElemsIds(['result-area'], false)
    initFormOnsubmitListener()
}


const scrollToResults = () => {
    document.getElementById('result-area').scrollIntoView()
}


const blink = async (elem) => {
    if (!!elem) {
        elem.hidden = true
        await new Promise(r => setTimeout(r, 100))
        elem.hidden = false
    }
}


const hideFormFields = (formId) => {
    const form = document.getElementById(formId)
    if (!!form) {
        [...form.elements].forEach(element => {
            if ($(element).is(':hidden') || element.type === 'submit') {
                return
            }
            // Скрывать чекбоксы не нужно: чекбокс передается в formData только если
            // он активен, в противном случае он не передается.
            // Получается, что если его скрыть, и он не был активирован при отправке
            // формы – обратно в интерфейсе формы после парсинга уникального кода он
            // не появится.
            if (element.type === 'checkbox') {
                element.checked = false
                return
            }
            if (element.type === 'radio') {
                document.getElementById(`div_id_${element.name}`).hidden = true
                return
            }
            document.getElementById(`div_${element.id}`).hidden = true
        })
    }
}


const setInvalidFormField = (formId, formFieldTitle, errors) => {
    const _setInvalidFormField = (field, errorText) => {
        field.classList.add("is-invalid")
        const errorDiv = document.createElement("div")
        errorDiv.classList.add("invalid-feedback", `${formId}-error-div`)
        errorDiv.innerText = errorText
        field.parentNode.insertBefore(errorDiv, field.nextSibling)
    }
    const formFieldId = `${formId}-${formFieldTitle}`
    const formField = document.getElementById(formFieldId)
    if (!!formField) {
        if (Array.isArray(errors)) {
            for (let error of errors) {
                _setInvalidFormField(formField, error)
            }
        } else {
            _setInvalidFormField(formField, errors)
        }
        return true
    }
    return false
}


const cleanFormErrorDivs = (formId) => {
    const form = document.getElementById(formId)
    if (!!form) {
        [...form.elements].forEach(field => {
            field.classList.remove("is-invalid")
        })
        document.querySelectorAll('.' + `${formId}-error-div`)
            .forEach((element) => element.remove())
    }
}


const disableForm = (form) => {
    [...form.elements].forEach((item) => {
        item.setAttribute('disabled', 'disabled')
    })
}


const enableForm = (form) => {
    [...form.elements].forEach((item) => {
        item.removeAttribute('disabled')
    })
}


const setSubmitButtonSpinner = (button) => {
    button.innerHTML = '<div class="spinner-border text-light spinner-border-sm" ' +
        'role="status"><span class="sr-only">Loading...</span></div>'
}


const hideSubmitButtonSpinner = (button, buttonText) => {
    button.innerHTML = buttonText
}


const getPayloadFromForm = (form) => {
    const payload = {};
    const errors = {};
    [...form.elements].forEach(element => {
        if (element.type === 'checkbox') {
            payload[element.name] = !!element.checked
        } else if (['choices', 'values'].includes(element.name)) {
            const value = element.value.replace('\n', '').replace('\r', '')
            try {
                payload[element.name] = JSON.parse(value)
            } catch {
                errors[element.name] = 'Некорректный JSON.'
            }
        } else if (!(element.type === 'hidden' || element.type === 'submit')) {
            if (element.type === 'number' && element.value === '') {
                payload[element.name] = null
            } else {
                payload[element.name] = element.value
            }
        }
    })
    return [payload, errors]
}


const asyncSleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))
