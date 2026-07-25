import { Box, CircularProgress } from '@mui/material';
import { Suspense, lazy, useState } from 'react';

import { IncidentCard } from '../components/IncidentCard';
import { NotificationPanel } from '../components/NotificationPanel';
import { RecommendationPanel } from '../components/RecommendationPanel';
import { SearchPanel } from '../components/SearchPanel';
import { StatusBar } from '../components/StatusBar';
import { TopToolbar } from '../components/TopToolbar';
import { DispatcherLayout } from '../layouts/DispatcherLayout';

// The map (Leaflet) is heavy — load it lazily / in its own chunk (code splitting).
const MapView = lazy(() => import('../components/MapView'));

/** The dispatcher workstation — assembles the panels around shared state. */
export function DispatcherPage() {
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  return (
    <>
      <DispatcherLayout
        top={
          <TopToolbar
            onSearch={(q) => {
              setSearchQuery(q);
              setSearchOpen(true);
            }}
            onOpenNotifications={() => setNotificationsOpen(true)}
          />
        }
        left={<IncidentCard />}
        center={
          <Suspense
            fallback={
              <Box
                sx={{
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <CircularProgress />
              </Box>
            }
          >
            <MapView />
          </Suspense>
        }
        right={<RecommendationPanel />}
        bottom={<StatusBar />}
      />
      <SearchPanel
        open={searchOpen}
        onClose={() => setSearchOpen(false)}
        initialQuery={searchQuery}
      />
      <NotificationPanel
        open={notificationsOpen}
        onClose={() => setNotificationsOpen(false)}
      />
    </>
  );
}
