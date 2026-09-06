from pathlib import Path
p=Path('NullSignalMVP/app/src/main/java/com/nullsignal/local/TransitInference.java')
p.write_text(r'''package com.nullsignal.local;

import android.content.Context;

/** Public-commute interpretation of Android's generic IN_VEHICLE transition. */
public class TransitInference {
    private static final long TRANSFER_WINDOW_MS = 30L * 60L * 1000L;

    public static void onTransition(Context c, String activity, boolean enter) {
        NullSignalDb db = NullSignalDb.get(c);
        MobilityStore ms = MobilityStore.get(c);
        long now = System.currentTimeMillis();
        MobilityStore.LocationRow l = ms.lastLocation();

        if ("in_vehicle".equals(activity) && enter) {
            if (l != null) {
                db.putState("transit_board_lat", String.valueOf(l.lat));
                db.putState("transit_board_lon", String.valueOf(l.lon));
                db.putState("transit_board_ts", String.valueOf(now));
                db.putState("last_transit_board_label", String.format(java.util.Locale.US, "%.6f, %.6f", l.lat, l.lon));
            }
            long previousExit = parse(db.getState("transit_exit_ts", "0"));
            long journey = parse(db.getState("mob_current_journey", "0"));
            if (previousExit > 0 && now - previousExit <= TRANSFER_WINDOW_MS && journey > 0) {
                int transfers = parseInt(db.getState("journey_transfer_count", "0")) + 1;
                db.putState("journey_transfer_count", String.valueOf(transfers));
                db.putState("last_transfer_wait_ms", String.valueOf(now - previousExit));
                ms.incrementJourneyTransfers(journey);
                EventEngine.record(c, "transit", "transit:transfer", "Commute engine", "Public-transit transfer detected", "Waited " + Math.round((now-previousExit)/60000.0) + " min before the next motorized segment");
            } else {
                EventEngine.record(c, "transit", "transit:board", "Commute engine", "Motorized transit segment started", "Boarding area retained from the latest GPS fix");
            }
            db.putState("transit_active", "1");
        }

        if ("in_vehicle".equals(activity) && !enter) {
            if (l != null) {
                db.putState("transit_exit_lat", String.valueOf(l.lat));
                db.putState("transit_exit_lon", String.valueOf(l.lon));
                db.putState("transit_exit_ts", String.valueOf(now));
                db.putState("last_transit_exit_lat", String.valueOf(l.lat));
                db.putState("last_transit_exit_lon", String.valueOf(l.lon));
                db.putState("last_transit_exit_ts", String.valueOf(now));
            }
            db.putState("transit_active", "0");
            long board = parse(db.getState("transit_board_ts", "0"));
            EventEngine.record(c, "transit", "transit:exit", "Commute engine", "Motorized transit segment ended", board>0?"Ride segment lasted "+Math.max(1,Math.round((now-board)/60000.0))+" min":"Exit position retained from the latest GPS fix");
        }

        if (enter && ("walking".equals(activity) || "still".equals(activity))) {
            long exit = parse(db.getState("transit_exit_ts", "0"));
            if (exit > 0 && now - exit < 10L * 60L * 1000L) {
                EventEngine.record(c, "transit", "transit:exit_confirmed", "Commute engine", "Transit exit confirmed", "Motorized movement was followed by "+activity);
            }
        }
    }

    private static long parse(String s){try{return Long.parseLong(s);}catch(Exception e){return 0;}}
    private static int parseInt(String s){try{return Integer.parseInt(s);}catch(Exception e){return 0;}}
}
''')
