import { create } from 'zustand'

interface ThemeState {
    theme: "dark" | "light"
    toggleTheme: () => void
}

const getInitialTheme = (): "dark" | "light" => {
    const stored = localStorage.getItem("theme")
    if (stored === "dark" || stored === "light") {
        return stored
    }
    return "dark"
}

export const useThemeStore = create<ThemeState>((set) => {
    const initialTheme = getInitialTheme()
    if (initialTheme === "dark") {
        document.documentElement.classList.add("dark")
    } else {
        document.documentElement.classList.remove("dark")
    }

    return {
        theme: initialTheme,
        toggleTheme: () => {
            set((state) => {
                const newTheme = state.theme === "dark" ? "light" : "dark"
                localStorage.setItem("theme", newTheme)
                if (newTheme === "dark") {
                    document.documentElement.classList.add("dark")
                } else {
                    document.documentElement.classList.remove("dark")
                }
                return { theme: newTheme }
            })
        }
    }
})
