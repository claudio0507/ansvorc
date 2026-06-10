import { useEffect } from "react"
import { useNavigate } from "react-router"
import { auth } from "~/lib/api"

export default function Index() {
  const navigate = useNavigate()
  useEffect(() => {
    navigate(auth.isLoggedIn() ? "/dashboard" : "/login", { replace: true })
  }, [navigate])
  return null
}
