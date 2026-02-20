import { useMemo } from "react";
import { Badge } from "@/components/ui/badge";
import { X } from "lucide-react";

export default function MultiSelect({
  options,
  value,
  onChange,
  max = 12,
}: {
  options: string[];
  value: string[];
  onChange: (next: string[]) => void;
  max?: number;
}) {
  const set = useMemo(() => new Set(value), [value]);

  function toggle(opt: string) {
    const next = new Set(set);
    if (next.has(opt)) next.delete(opt);
    else {
      if (next.size >= max) return; // cap
      next.add(opt);
    }
    onChange(Array.from(next));
  }

  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => {
        const active = set.has(opt);
        return (
          <Badge
            key={opt}
            variant={active ? "default" : "outline"}
            className={`cursor-pointer transition-all hover:scale-105 ${
              active ? "bg-primary text-primary-foreground" : "hover:bg-muted"
            }`}
            onClick={() => toggle(opt)}
          >
            {opt}
            {active && <X className="ml-1 h-3 w-3" />}
          </Badge>
        );
      })}
    </div>
  );
}
