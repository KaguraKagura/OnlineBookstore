// create a form and add csrf
function prepareForm(csrfToken) {
    let form = document.createElement('form');
    form.method = 'post';
    let csrfField = document.createElement('input');
    csrfField.type = 'hidden';
    csrfField.name = 'csrfmiddlewaretoken';
    csrfField.value = csrfToken;
    form.appendChild(csrfField);
    return form;
}
