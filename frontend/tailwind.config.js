/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: '#EB5A23',
                dark: '#000000',
                light: '#FFFFFF',
                'dark-gray': '#434040',
            },
            fontFamily: {
                sans: ['Ruda', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
