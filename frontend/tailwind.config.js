/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Georgia", "serif"],
        body: ["ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        ink: "#1f2937",
        paper: "#fcfaf5",
        ember: "#b45309",
        slateblue: "#1d3557",
        sage: "#6b8f71",
      },
      boxShadow: {
        panel: "0 24px 60px rgba(17, 24, 39, 0.12)",
      },
      backgroundImage: {
        "paper-grid":
          "radial-gradient(circle at 1px 1px, rgba(29,53,87,0.12) 1px, transparent 0)",
      },
    },
  },
  plugins: [],
};
