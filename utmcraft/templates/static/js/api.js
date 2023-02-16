const FormHTMLRoute = '/core/api/form_html'
const ResultBlocksHTMLRoute = '/core/api/result_blocks_html'
const ParserRoute = '/core/api/parser'
const ClientAdminInputTextRoute = '/settings/api/v1/input-text/'
const ClientAdminInputIntRoute = '/settings/api/v1/input-int/'
const ClientAdminCheckboxRoute = '/settings/api/v1/checkbox/'
const ClientAdminRadioButtonRoute = '/settings/api/v1/radiobutton/'
const ClientAdminSelectRoute = '/settings/api/v1/select/'
const ClientAdminSelectDepsRoute = '/settings/api/v1/select-deps/'


const fetchFormHTML = async (formId) => {
    const response = await fetch(FormHTMLRoute + '?' + new URLSearchParams({form_id: formId}))
    return await response.text()
}


const fetchResultBlocksHTML = async (data) => {
    const response = await fetch(ResultBlocksHTMLRoute, {
        method: 'POST',
        headers: {
            'X-CSRFToken': Cookies.get('csrftoken'),
            'Content-Type': 'application/json'
        },
        mode: 'same-origin',
        body: data
    })
    return await response.text()
}


const fetchParserData = async (utmHashcode) => {
    const response = await fetch(ParserRoute + '?' + new URLSearchParams({utm_hashcode: utmHashcode}))
    if (response.status === 500) {
        return {'error': 'Сервис временно недоступен 😔'}
    }
    return await response.json()
}


const patchClientAdmin = async (payload, entityId, route) => {
    const fullRoute = route + entityId + "/"
    const response = await fetch(fullRoute, {
        method: 'PATCH',
        headers: {
            'X-CSRFToken': Cookies.get('csrftoken'),
            'Content-Type': 'application/json'
        },
        mode: 'same-origin',
        body: JSON.stringify(payload)
    });
    const result = await response.json()
    const status = response.status
    return {"statusCode": status, "data": result}
}
