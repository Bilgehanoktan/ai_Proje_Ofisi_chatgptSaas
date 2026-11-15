import type { ReactNode } from 'react';
import './globals.css';
import '../design-system/eds.css';
import ThemeFrame from '../design-system/ThemeFrame';
export default function Layout({children}:{children:ReactNode}) { return <html lang="tr"><body><ThemeFrame>{children}</ThemeFrame></body></html> }
