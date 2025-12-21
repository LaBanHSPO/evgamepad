import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useGamepad } from "@/hooks/useGamepad";

export const GlobalGamepadHandler = () => {
    // Initialize gamepad polling globally
    useGamepad();

    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Monitor Switching Logic
            // [ = Prev Monitor (LT)
            // ] = Next Monitor (RT)

            const routes = ["/", "/m2", "/m3"];
            const currentPath = location.pathname;
            const currentIndex = routes.indexOf(currentPath); // -1 if not found

            if (currentIndex === -1) return; // Don't switch if on unknown route (e.g. 404)

            if (e.key === "[") {
                const nextIndex = (currentIndex - 1 + routes.length) % routes.length;
                navigate(routes[nextIndex]);
            } else if (e.key === "]") {
                const nextIndex = (currentIndex + 1) % routes.length;
                navigate(routes[nextIndex]);
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [navigate, location]);

    return null; // Logic only component
};
