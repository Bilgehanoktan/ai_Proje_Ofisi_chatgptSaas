import type { ReactNode } from 'react';
import './globals.css';
import '../design-system/eds.css';
import ThemeFrame from '../design-system/ThemeFrame';
import {SharedSnapshotProvider} from '../features/data/SharedSnapshotProvider';
export default function Layout({children}:{children:ReactNode}) { return <html lang="tr"><body><ThemeFrame><SharedSnapshotProvider>{children}</SharedSnapshotProvider></ThemeFrame></body></html> }
