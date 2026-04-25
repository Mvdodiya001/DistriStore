/**
 * Button — Reusable button with variants, loading state, and icon support.
 */

import clsx from 'clsx'

const VARIANTS = {
  primary: 'btn btn-primary',
  success: 'btn btn-success',
  danger: 'btn btn-danger',
  secondary: 'btn btn-secondary',
  ghost: 'btn-copy',
  download: 'btn-copy btn-dl',
}

export default function Button({
  children,
  variant = 'primary',
  loading = false,
  disabled = false,
  icon,
  className,
  ...props
}) {
  return (
    <button
      className={clsx(VARIANTS[variant] || VARIANTS.primary, className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <div className="spinner" />}
      {!loading && icon && <span className="btn-icon">{icon}</span>}
      {children}
    </button>
  )
}
