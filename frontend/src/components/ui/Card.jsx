/**
 * Card — Reusable panel component with icon, title, and glassmorphism styling.
 */

import clsx from 'clsx'

export default function Card({ children, title, icon, className, noPad, ...props }) {
  return (
    <div className={clsx('panel', className)} {...props}>
      {(title || icon) && (
        <div className="panel-title">
          {icon && <span className="icon">{icon}</span>}
          {title}
        </div>
      )}
      <div className={clsx(!noPad && 'card-body')}>
        {children}
      </div>
    </div>
  )
}
