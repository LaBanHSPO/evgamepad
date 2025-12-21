import { useEffect, useRef } from "react";

// Xbox Controller Standard Mapping (Standard Gamepad API)
// Buttons:
// 0: A
// 1: B
// 2: X
// 3: Y
// 4: LB
// 5: RB
// 6: LT (Analog, but often registers as button too)
// 7: RT
// 8: Back/View
// 9: Start/Menu
// 10: Left Stick Click
// 11: Right Stick Click
// 12: D-Pad Up
// 13: D-Pad Down
// 14: D-Pad Left
// 15: D-Pad Right

// Axes:
// 0: Left Stick X
// 1: Left Stick Y
// 2: Right Stick X
// 3: Right Stick Y

interface GamepadConfig {
    enableScrolling?: boolean;
    scrollSpeed?: number;
}

export const useGamepad = (config: GamepadConfig = {}) => {
    const { enableScrolling = true, scrollSpeed = 15 } = config;
    const requestRef = useRef<number>();
    const lastPressedRef = useRef<Set<number>>(new Set());
    const lastScrollTimeRef = useRef<number>(0);

    useEffect(() => {
        const pollGamepad = () => {
            const gamepads = navigator.getGamepads();
            const gp = gamepads[0]; // Assuming player 1

            if (gp) {
                const pressed = new Set<number>();

                // Check Buttons
                gp.buttons.forEach((btn, index) => {
                    if (btn.pressed) {
                        pressed.add(index);

                        // Trigger on PRESS (rising edge)
                        if (!lastPressedRef.current.has(index)) {
                            handleButtonPress(index);
                        }
                    }
                });

                lastPressedRef.current = pressed;

                // Check Axes for Scrolling
                if (enableScrolling) {
                    const now = Date.now();
                    if (now - lastScrollTimeRef.current > 16) { // Cap at ~60fps
                        const rightStickY = gp.axes[3];
                        if (Math.abs(rightStickY) > 0.2) { // Deadzone
                            window.scrollBy(0, rightStickY * scrollSpeed);
                            lastScrollTimeRef.current = now;
                        }
                    }
                }
            }

            requestRef.current = requestAnimationFrame(pollGamepad);
        };

        const handleButtonPress = (buttonIndex: number) => {
            let key = "";

            switch (buttonIndex) {
                case 0: key = "Enter"; break; // A -> Confirm
                case 1: key = "b"; break;     // B -> Back/Close
                case 2: key = "x"; break;     // X -> Action/Modify
                case 3: key = "y"; break;     // Y -> Alternative Action
                case 4: key = "q"; break;     // LB -> Tab Left
                case 5: key = "e"; break;     // RB -> Tab Right
                case 6: key = "["; break;     // LT -> Prev Monitor
                case 7: key = "]"; break;     // RT -> Next Monitor
                case 8: key = "m"; break;     // Back/View -> Mute
                case 9: key = "p"; break;     // Start/Menu -> Play
                case 10: key = "v"; break;    // L3 -> Talk
                case 12: key = "ArrowUp"; break;
                case 13: key = "ArrowDown"; break;
                case 14: key = "ArrowLeft"; break;
                case 15: key = "ArrowRight"; break;
            }

            if (key) {
                // Dispatch synthetic event
                const event = new KeyboardEvent("keydown", {
                    key: key,
                    code: key,
                    bubbles: true,
                    cancelable: true,
                    view: window,
                });
                window.dispatchEvent(event);
            }
        };

        requestRef.current = requestAnimationFrame(pollGamepad);

        return () => {
            if (requestRef.current) {
                cancelAnimationFrame(requestRef.current);
            }
        };
    }, [enableScrolling, scrollSpeed]);
};
