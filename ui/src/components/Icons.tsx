import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function IconFrame({ children, ...props }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      {children}
    </svg>
  );
}

export function SparkIcon(props: IconProps) {
  return (
    <IconFrame {...props}>
      <path d="M12 3l1.35 4.15L17.5 8.5l-4.15 1.35L12 14l-1.35-4.15L6.5 8.5l4.15-1.35L12 3Z" />
      <path d="m18 14 .72 2.28L21 17l-2.28.72L18 20l-.72-2.28L15 17l2.28-.72L18 14Z" />
    </IconFrame>
  );
}

export function ShieldIcon(props: IconProps) {
  return (
    <IconFrame {...props}>
      <path d="M12 3 5.5 5.7v5.55c0 4.2 2.62 7.85 6.5 9.25 3.88-1.4 6.5-5.05 6.5-9.25V5.7L12 3Z" />
      <path d="m9 12 2 2 4-4" />
    </IconFrame>
  );
}

export function ReviewIcon(props: IconProps) {
  return (
    <IconFrame {...props}>
      <path d="M7 4.5h10A1.5 1.5 0 0 1 18.5 6v12A1.5 1.5 0 0 1 17 19.5H7A1.5 1.5 0 0 1 5.5 18V6A1.5 1.5 0 0 1 7 4.5Z" />
      <path d="M9 4.5V3h6v1.5M9 9h6m-6 4h6m-6 4h3" />
    </IconFrame>
  );
}

export function DatabaseIcon(props: IconProps) {
  return (
    <IconFrame {...props}>
      <ellipse cx="12" cy="5.5" rx="7" ry="3" />
      <path d="M5 5.5v6c0 1.66 3.13 3 7 3s7-1.34 7-3v-6" />
      <path d="M5 11.5v6c0 1.66 3.13 3 7 3s7-1.34 7-3v-6" />
    </IconFrame>
  );
}

export function ArrowIcon(props: IconProps) {
  return (
    <IconFrame {...props}>
      <path d="M5 12h14m-5-5 5 5-5 5" />
    </IconFrame>
  );
}

export function RefreshIcon(props: IconProps) {
  return (
    <IconFrame {...props}>
      <path d="M20 6v5h-5" />
      <path d="M18.1 16A8 8 0 1 1 20 11" />
    </IconFrame>
  );
}

export function CheckIcon(props: IconProps) {
  return (
    <IconFrame {...props}>
      <path d="m5 12 4 4L19 6" />
    </IconFrame>
  );
}

export function CloseIcon(props: IconProps) {
  return (
    <IconFrame {...props}>
      <path d="m7 7 10 10M17 7 7 17" />
    </IconFrame>
  );
}

export function ClockIcon(props: IconProps) {
  return (
    <IconFrame {...props}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5V12l3 2" />
    </IconFrame>
  );
}

export function QuoteIcon(props: IconProps) {
  return (
    <IconFrame {...props}>
      <path d="M9.5 10H6.8A2.8 2.8 0 0 0 4 12.8V17h5.5v-7Zm10 0h-2.7a2.8 2.8 0 0 0-2.8 2.8V17h5.5v-7Z" />
      <path d="M4.2 12.5C4.5 8.8 6.2 6.4 9 5m5.2 7.5c.3-3.7 2-6.1 4.8-7.5" />
    </IconFrame>
  );
}
