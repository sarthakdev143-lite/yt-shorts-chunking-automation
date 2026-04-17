import { cn } from "@/lib/utils";

type SwitchProps = {
  checked: boolean;
  onChange?: (checked: boolean) => void;
  name?: string;
};

export function Switch({ checked, onChange, name }: SwitchProps) {
  return (
    <label className="inline-flex cursor-pointer items-center gap-3">
      <input
        checked={checked}
        className="sr-only"
        name={name}
        onChange={(event) => onChange?.(event.target.checked)}
        type="checkbox"
      />
      <span
        className={cn(
          "relative inline-flex h-7 w-12 items-center rounded-full border transition",
          checked
            ? "border-[color:var(--accent)] bg-[color:var(--accent)]/35"
            : "border-[color:var(--line)] bg-white/5",
        )}
      >
        <span
          className={cn(
            "absolute left-1 h-5 w-5 rounded-full bg-white shadow-[0_6px_18px_rgba(0,0,0,0.3)] transition",
            checked && "translate-x-5 bg-[color:var(--accent)]",
          )}
        />
      </span>
    </label>
  );
}
