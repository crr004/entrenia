export const userValidationRegex = {
    username: /^(?=(?:.*[a-z]){3})[a-z0-9_]+$/,
    fullname: /^[A-Za-zÁ-ÿà-ÿ]+(?:[ '-][A-Za-zÁ-ÿà-ÿ]+)*$/,
    email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
}