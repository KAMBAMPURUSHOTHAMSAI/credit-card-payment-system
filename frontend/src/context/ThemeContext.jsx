import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";


const ThemeContext = createContext(null);


const THEME_STORAGE_KEY = "creditpay_theme";


export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem(
      THEME_STORAGE_KEY
    );

    if (
      savedTheme === "light" ||
      savedTheme === "dark"
    ) {
      return savedTheme;
    }

    return "light";
  });


  useEffect(() => {
    const root = document.documentElement;

    root.classList.toggle(
      "dark",
      theme === "dark"
    );

    root.style.colorScheme = theme;

    localStorage.setItem(
      THEME_STORAGE_KEY,
      theme
    );
  }, [theme]);


  const toggleTheme = () => {
    setTheme((currentTheme) =>
      currentTheme === "dark"
        ? "light"
        : "dark"
    );
  };


  const value = {
    theme,
    setTheme,
    toggleTheme,
    isDark: theme === "dark",
  };


  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}


// eslint-disable-next-line react-refresh/only-export-components
export function useTheme() {
  const context = useContext(
    ThemeContext
  );

  if (!context) {
    throw new Error(
      "useTheme must be used inside ThemeProvider."
    );
  }

  return context;
}