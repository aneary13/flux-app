"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface SliderProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange" | "value"> {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ className, value, onChange, min = 0, max = 10, step = 1, ...props }, ref) => {
    return (
      <input
        type="range"
        ref={ref}
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className={cn(
          "w-full h-2 rounded-full appearance-none bg-neutral-200 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-neutral-800 [&::-webkit-slider-thumb]:cursor-pointer",
          "accent-[#8DA887]",
          className
        )}
        {...props}
      />
    );
  }
);
Slider.displayName = "Slider";

export { Slider };
