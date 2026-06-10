/** Dark mode — port de toggleDarkMode/applyStoredTheme (app.js). */
import { useEffect, useState } from "react"

const KEY = "sinalys_dark"

export function applyStoredTheme() {
  if (typeof document === "undefined") return
  if (localStorage.getItem(KEY) === "1") {
    document.documentElement.classList.add("dark")
  }
}

export function useDarkMode(): [boolean, () => void] {
  const [isDark, setIsDark] = useState(
    () => typeof document !== "undefined" && document.documentElement.classList.contains("dark")
  )

  useEffect(() => {
    setIsDark(document.documentElement.classList.contains("dark"))
  }, [])

  const toggle = () => {
    const next = document.documentElement.classList.toggle("dark")
    localStorage.setItem(KEY, next ? "1" : "0")
    setIsDark(next)
  }

  return [isDark, toggle]
}
