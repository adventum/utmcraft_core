const initSelect2 = () => {
    $('.form-select2').select2({
        theme: 'bootstrap4',
        language: 'ru'
    })
    $('.form-select2-no-search').select2({
        theme: 'bootstrap4',
        language: 'ru',
        minimumResultsForSearch: Infinity
    })
}


const initTooltips = () => {
    $('[data-toggle="tooltip"]').tooltip()
}


const initCustomValuesFields = () => {
    const customValuesFields = document.querySelectorAll('*[id^="div_id_custom-"]')
    customValuesFields.forEach(element => {
        setIsVisibleByElemsIds([element.id], false)
        const parentFieldId = element.id.replace('div_id_custom-', 'id_')
        let parentField = document.getElementById(parentFieldId)
        try {
            if (parentField === null) {
                const radioButtonElems = document.querySelectorAll(`*[id^=${parentFieldId}]`)
                radioButtonElems.forEach(rbElem => {
                    rbElem.onchange = () => {
                        if (rbElem.checked) {
                            setIsVisibleByElemsIds([element.id], rbElem.value === 'custom-value-input-field')
                        }
                    }
                })
            } else {
                parentField.oninput = () => {
                    setIsVisibleByElemsIds([element.id], parentField.value === 'custom-value-input-field')
                }
            }
        } catch {
        }
    })
}


const initFormContainer = () => {
    showSpinner()
    initCustomValuesFields()
    initSelectDependencies()
    document.getElementById('main-container').hidden = false
    hideSpinner()
}


const initFormSelector = () => {
    const formChoices = document.getElementsByClassName('form-selector-choice')
    for (let elem of formChoices) {
        elem.onclick = async () => {
            showSpinner()
            await fetchAndSetForm(elem.getAttribute('formId'))
            hideSpinner()
        }
    }
}


const initClipboardButtons = () => {
    new ClipboardJS('.btn-clipboard')
}


const initFormOnsubmitListener = () => {
    const form = document.getElementById('builder-form')

    const getUtmBuilderData = () => {
        const form = document.getElementById('builder-form')
        const formdata = new FormData(form)
        const data = {
            form_id: 0,
            form_data: {},
        }
        for (let pair of formdata.entries()) {
            const name = pair[0]
            const value = pair[1]
            if (name === 'form_id') {
                data.form_id = value
                continue
            }
            if (name === 'csrfmiddlewaretoken') {
                continue
            }
            if (name === 'build') {
                continue
            }
            data.form_data[name] = value
        }
        return JSON.stringify(data)
    }

    if (!!form) {
        form.onsubmit = async (e) => {
            e.preventDefault()
            showSpinner()
            const rawData = getUtmBuilderData()
            const resultData = await fetchResultBlocksHTML(rawData)
            const resultArea = document.getElementById('result-area')
            resultArea.innerHTML = resultData
            initClipboardButtons()
            setIsVisibleByElemsIds(['result-area'], true)
            scrollToResults()
            hideSpinner()
        }
    }
}


const initSelectDependencies = () => {
    const selectDependencies = document.getElementById('select-dependencies-data')
    if (!selectDependencies) {
        return
    }
    try {
        const data = JSON.parse(selectDependencies.textContent)
        for (const dependence of data) {
            const childField = document.getElementById(`id_${dependence['child_field']}`)
            const parentFields = document.getElementsByName(dependence['parent_field'])
            if (!childField || !parentFields) {
                continue
            }
            let childFieldIsInitialState = true
            let childFieldInitialActiveOptionValue
            const childFieldInitOptions = {}
            for (const option of childField.options) {
                childFieldInitOptions[option.text] = option.value
                if (option.selected) {
                    childFieldInitialActiveOptionValue = option.value
                }
            }

            const setInitialOptions = () => {
                const childField = $(`#id_${dependence['child_field']}`)
                if (childFieldIsInitialState === false) {
                    childField.empty()
                    for (const [label, value] of Object.entries(childFieldInitOptions)) {
                        const newOption = new Option(label, value, false, false)
                        childField.append(newOption)
                    }
                    childField.val(childFieldInitialActiveOptionValue).trigger('change.select2')
                    childFieldIsInitialState = true
                }
            }

            const setDependenceOptions = (parentValue) => {
                for (const [parentValueDep, childLabels] of Object.entries(dependence['values'])) {
                    if (parentValue === parentValueDep) {
                        const childField = $(`#id_${dependence['child_field']}`)
                        childField.empty()
                        for (const label of childLabels) {
                            const newOption = new Option(label, childFieldInitOptions[label], false, false)
                            childField.append(newOption)
                        }
                        childField.trigger('change.select2')
                        childFieldIsInitialState = false
                        return
                    }
                }
                setInitialOptions()
            }

            // Radio Buttons
            if (parentFields.length > 1) {
                for (const radioButton of parentFields) {
                    $(radioButton).on('change', () => {
                        if (radioButton.checked) {
                            setDependenceOptions(radioButton.value)
                        }
                    })
                }
                continue
            }
            // Остальные элементы
            const parentField = parentFields[0]
            switch (parentField.type) {
                case 'select-one':
                    setDependenceOptions(parentField.value)
                    $(parentField).on('change.select2', () => {
                        setDependenceOptions(parentField.value)
                    })
                    break
                case 'text':
                case 'number':
                    setDependenceOptions(parentField.value)
                    $(parentField).on('input', () => {
                        setDependenceOptions(parentField.value)
                    })
                    break
                case 'checkbox':
                    setDependenceOptions(parentField.checked ? 'on' : 'off')
                    $(parentField).on('change', () => {
                        setDependenceOptions(parentField.checked ? 'on' : 'off')
                    })
                    break
            }
        }
    } catch {
    }
}


const initModalListeners = () => {
    const parserModal = $('#parser-modal')
    const instructionModal = $('#instruction-modal')

    const makeFormSelectorWhite = () => {
        const utmFormSelector = document.getElementById('nav-form-selector')
        if (!!utmFormSelector) {
            utmFormSelector.classList.remove('advm-green-color')
            utmFormSelector.classList.add('white-color')
        }
    }

    const makeFormSelectorGreen = () => {
        const utmFormSelector = document.getElementById('nav-form-selector')
        if (!!utmFormSelector) {
            utmFormSelector.classList.remove('white-color')
            utmFormSelector.classList.add('advm-green-color')
        }
    }

    parserModal.on('show.bs.modal', () => {
        const navParserButton = document.getElementById('nav-parser')
        if (!!navParserButton) {
            navParserButton.classList.remove('white-color')
            navParserButton.classList.add('advm-green-color')
        }
        makeFormSelectorWhite()

    })
    parserModal.on('hidden.bs.modal', () => {
        const navParserButton = document.getElementById('nav-parser')
        if (!!navParserButton) {
            navParserButton.classList.remove('advm-green-color')
            navParserButton.classList.add('white-color')
        }
        makeFormSelectorGreen()
    })
    instructionModal.on('show.bs.modal', () => {
        const instructionParserButton = document.getElementById('nav-instruction')
        if (!!instructionParserButton) {
            instructionParserButton.classList.remove('white-color')
            instructionParserButton.classList.add('advm-green-color')
        }
        makeFormSelectorWhite()
    })
    instructionModal.on('hidden.bs.modal', () => {
        const instructionParserButton = document.getElementById('nav-instruction')
        if (!!instructionParserButton) {
            instructionParserButton.classList.remove('advm-green-color')
            instructionParserButton.classList.add('white-color')
        }
        makeFormSelectorGreen()
    })
}


const initParser = () => {
    const parserForm = document.getElementById('parser-form')

    const showParserAlert = async (message) => {
        const alert = document.getElementById('parser-form-alert')
        if (!!alert) {
            alert.textContent = message
            if (alert.hidden === false) {
                await blink(alert)
            } else {
                alert.hidden = false
            }
        }
    }

    const hideParserAlert = () => {
        const alert = document.getElementById('parser-form-alert')
        if (!!alert) {
            alert.hidden = true
        }
    }

    const setUpFormData = (formData) => {
        for (const [fieldPk, value] of Object.entries(formData)) {
            if (fieldPk.startsWith('custom-') && !value) {
                continue
            }
            const fieldId = `id_${fieldPk}`
            const field = document.getElementById(fieldId) || document.getElementById(`${fieldId}_0`)
            if (!!field) {
                switch (field.type) {
                    case 'text':
                    case 'number':
                        field.value = value
                        break
                    case 'select-one':
                        $(field).val(value).trigger('change')
                        break
                    case 'checkbox':
                        field.checked = value === 'on'
                        break
                    case 'radio':
                        field.checked = field.value === value
                        if (field.checked === true) {
                            break
                        }
                        let i = 1
                        while (true) {
                            const radioButton = document.getElementById(`${fieldId}_${i}`)
                            if (!radioButton) {
                                break
                            }
                            radioButton.checked = radioButton.value === value
                            if (radioButton.checked === true) {
                                break
                            } else {
                                i++
                            }
                        }
                        break
                }
                document.getElementById(`div_${fieldId}`).hidden = false
            }
        }
    }

    if (!!parserForm) {
        parserForm.onsubmit = async (e) => {
            e.preventDefault()
            const utmHashcodeField = document.getElementById('utm-parser-code-input')
            if (!utmHashcodeField) {
                return
            }
            const utmHashcode = utmHashcodeField.value
            if (utmHashcode.length !== 8) {
                await showParserAlert('Неверный код.')
                return
            }
            showSpinner()
            const result = await fetchParserData(utmHashcode)
            if (!!result.error) {
                await showParserAlert(result.error)
                hideSpinner()
                return
            }
            const formId = document.getElementById('id_form_id')
            if (!formId || (formId.value !== result.form_id.toString())) {
                await fetchAndSetForm(result.form_id.toString())
            }
            setIsVisibleByElemsIds(['result-area'], false)
            hideFormFields('builder-form')
            setUpFormData(result.form_data)
            $('#parser-modal').modal('hide')
            hideParserAlert()
            hideSpinner()
        }
    }
}


const initClientAdminSearchFormListener = () => {
    const form = document.getElementById('search-client-admin-form')
    if (!!form) {
        form.onsubmit = (e) => {
            e.preventDefault()
        }
    }
    const selectField = document.getElementById('search-client-admin-select')
    if (!!selectField) {
        selectField.onchange = () => {
            try {
                const select = document.getElementById('search-client-admin-select')
                window.location.href = select.options[select.selectedIndex].getAttribute('url')
            } catch {
            }
        }
    }
}


const initClientAdminPatchForms = () => {
    const onClientAdminPatchFormSubmit = async (form, route) => {
        const entityId = form.getAttribute("entityId")
        const alert = document.getElementById(`patch-${entityId}-modal-alert`)
        const modal = $(`#patch-${entityId}-modal`)
        const submitButton = document.getElementById(`${form.id}-submit-button`)
        const submitButtonText = submitButton.textContent
        cleanFormErrorDivs(form.id)
        alert.hidden = true
        disableForm(form)
        setSubmitButtonSpinner(submitButton)
        let payload, payloadValidationErrors
        [payload, payloadValidationErrors] = getPayloadFromForm(form)
        if (Object.keys(payloadValidationErrors).length > 0) {
            await asyncSleep(100)
            for (let field in payloadValidationErrors) {
                setInvalidFormField(form.id, field, payloadValidationErrors[field])
            }
            hideSubmitButtonSpinner(submitButton, submitButtonText)
            enableForm(form)
            return
        }
        const result = await patchClientAdmin(payload, entityId, route)
        if (result.statusCode !== 200) {
            if (result.data && typeof (result.data) === "object") {
                for (let field in result.data) {
                    const isSet = setInvalidFormField(form.id, field, result.data[field])
                    if (isSet === true) {
                        delete result.data[field]
                    }
                }
            }
            if (Object.keys(result.data).length !== 0) {
                alert.hidden = false
                const errors = []
                for (let field in result.data) {
                    const fieldErrors = result.data[field]
                    if (Array.isArray(fieldErrors)) {
                        for (let error of fieldErrors) {
                            errors.push(error)
                        }
                    } else {
                        errors.push(fieldErrors)
                    }
                }
                alert.innerHTML = errors.join("<hr>")
            }
            hideSubmitButtonSpinner(submitButton, submitButtonText)
            enableForm(form)
            return
        }
        modal.modal('hide')
        location.reload()
    }
    const entities = [
        {type: 'input-text', route: ClientAdminInputTextRoute},
        {type: 'input-int', route: ClientAdminInputIntRoute},
        {type: 'checkbox', route: ClientAdminCheckboxRoute},
        {type: 'radio-button', route: ClientAdminRadioButtonRoute},
        {type: 'select', route: ClientAdminSelectRoute},
        {type: 'select-deps', route: ClientAdminSelectDepsRoute},
    ]
    for (let entity of entities) {
        const forms = document.getElementsByClassName(`${entity.type}-patch-form`)
        for (let form of forms) {
            form.addEventListener("submit", async (e) => {
                e.preventDefault()
                await onClientAdminPatchFormSubmit(e.target, entity.route)
            })
        }
    }
}
