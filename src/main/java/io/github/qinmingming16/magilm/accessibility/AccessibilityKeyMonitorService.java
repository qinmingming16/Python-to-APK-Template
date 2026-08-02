package io.github.qinmingming16.magilm.accessibility;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.accessibilityservice.GestureDescription;
import android.graphics.Path;
import android.view.KeyEvent;
import android.view.accessibility.AccessibilityEvent;
import java.util.HashMap;

public class AccessibilityKeyMonitorService extends AccessibilityService {
    private static HashMap<String, int[]> keyMap = new HashMap<>();
    private static boolean isRunning = false;
    private static AccessibilityKeyMonitorService instance = null;

    @Override
    public void onCreate() {
        super.onCreate();
        instance = this;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        instance = null;
    }

    public static void setKeyMap(String keyName, int x, int y) {
        keyMap.put(keyName, new int[]{x, y});
    }

    public static void startMap() {
        isRunning = true;
    }

    public static void stopMap() {
        isRunning = false;
        keyMap.clear();
    }

    public static boolean isServiceRunning() {
        return instance != null;
    }

    @Override
    public void onServiceConnected() {
        super.onServiceConnected();
        AccessibilityServiceInfo info = new AccessibilityServiceInfo();
        info.flags = AccessibilityServiceInfo.FLAG_REQUEST_FILTER_KEY_EVENTS;
        info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC;
        setServiceInfo(info);
    }

    @Override
    public boolean onKeyEvent(KeyEvent event) {
        if (!isRunning) return super.onKeyEvent(event);
        if (event.getAction() != KeyEvent.ACTION_DOWN) return super.onKeyEvent(event);

        int keyCode = event.getKeyCode();
        String keyName = keyCodeToKeyName(keyCode);

        if (keyMap.containsKey(keyName)) {
            int[] pos = keyMap.get(keyName);
            execClick(pos[0], pos[1]);
            return true;
        }

        return super.onKeyEvent(event);
    }

    private void execClick(int x, int y) {
        try {
            Path path = new Path();
            path.moveTo(x, y);
            GestureDescription.Builder builder = new GestureDescription.Builder();
            builder.addStroke(new GestureDescription.StrokeDescription(path, 0, 50));
            dispatchGesture(builder.build(), null, null);
        } catch (Exception ignored) {}
    }

    private String keyCodeToKeyName(int keyCode) {
        switch (keyCode) {
            // 字母 A-Z
            case 29: return "A"; case 30: return "B"; case 31: return "C"; case 32: return "D";
            case 33: return "E"; case 34: return "F"; case 35: return "G"; case 36: return "H";
            case 37: return "I"; case 38: return "J"; case 39: return "K"; case 40: return "L";
            case 41: return "M"; case 42: return "N"; case 43: return "O"; case 44: return "P";
            case 45: return "Q"; case 46: return "R"; case 47: return "S"; case 48: return "T";
            case 49: return "U"; case 50: return "V"; case 51: return "W"; case 52: return "X";
            case 53: return "Y"; case 54: return "Z";

            // 数字 0-9
            case 7: return "0"; case 8: return "1"; case 9: return "2"; case 10: return "3";
            case 11: return "4"; case 12: return "5"; case 13: return "6"; case 14: return "7";
            case 15: return "8"; case 16: return "9";

            // 符号键
            case 55: return ",";    // ,
            case 56: return ".";    // .
            case 76: return "/";    // /
            case 74: return ";";    // ;
            case 75: return "'";    // '
            case 69: return "-";    // -
            case 70: return "=";    // =
            case 68: return "`";    // `
            case 71: return "[";    // [
            case 72: return "]";    // ]
            case 73: return "\\";   // \

            // 控制键
            case 61: return "TAB";
            case 62: return "SPACE";
            case 66: return "ENTER";
            case 67: return "BACKSPACE";

            // 方向键
            case 19: return "UP";
            case 20: return "DOWN";
            case 21: return "LEFT";
            case 22: return "RIGHT";

            // 音量键
            case 24: return "VOLUME_UP";
            case 25: return "VOLUME_DOWN";

            default: return null;
        }
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {}
    @Override
    public void onInterrupt() {}
}

