/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        // canonical palette
        cef: {
          violet: "#39037E",
          lilac:  "#B49BFF",
          orange: "#FA6B12",
          rose:   "#FFBAE8",
          mint:   "#BAE0DE",
          yellow: "#FCFAC7",
          white:  "#FFFFFF",
        },
        // aliases to match your current class names
        "cefora-violet": "#39037E",
        "secondary-lilac": "#B49BFF",
        "secondary-orange": "#FA6B12",
        "tertiary-rose": "#FFBAE8",
        "tertiary-mint": "#BAE0DE",
        "tertiary-yellow": "#FCFAC7",
      },
      fontFamily: {
        rubik: ['"Rubik"', "Arial", "sans-serif"],
      },
      boxShadow: {
        card: "0 12px 28px rgba(57,3,126,0.12)",
      },
      borderRadius: {
        '2xl': "1rem",
      },
    },
  },
  plugins: [],
};
