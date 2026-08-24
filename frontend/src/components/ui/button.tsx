import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-base font-display font-semibold transition-all duration-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        // Boutons « 3D » : ombre pleine décalée vers le bas qui disparaît au clic
        // pendant que le bouton s'enfonce (signature tactile des apps gamifiées).
        default:
          "bg-primary text-primary-foreground shadow-[0_5px_0_var(--fun-green-dark)] hover:brightness-105 active:translate-y-[5px] active:shadow-none",
        destructive:
          "bg-destructive text-destructive-foreground shadow-[0_5px_0_#b91c1c] hover:brightness-105 active:translate-y-[5px] active:shadow-none",
        outline:
          "border-2 border-input bg-background text-foreground shadow-[0_4px_0_var(--fun-border)] hover:bg-accent hover:text-accent-foreground active:translate-y-[4px] active:shadow-none",
        secondary:
          "bg-secondary text-secondary-foreground shadow-[0_4px_0_#e8b98f] hover:brightness-105 active:translate-y-[4px] active:shadow-none",
        ghost: "hover:bg-accent hover:text-accent-foreground active:scale-95",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-11 px-5 py-2.5",
        sm: "h-9 rounded-xl px-3 text-sm",
        lg: "h-12 rounded-xl px-8 text-lg",
        icon: "h-11 w-11",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends
    React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
