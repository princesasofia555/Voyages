package com.voyages.memories;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {
    private static final int CREATE_BACKUP_FILE = 1001;
    private static final int OPEN_RESTORE_FILE = 1002;
    private static final int OPEN_PHOTO_FILE = 1003;
    private int pendingChooserRequestCode = OPEN_RESTORE_FILE;
    private WebView webView;
    private String pendingBackup;
    private ValueCallback<Uri[]> pendingFileChooser;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        webView = new WebView(this);
        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback,
                                             FileChooserParams params) {
                if (pendingFileChooser != null) pendingFileChooser.onReceiveValue(null);
                pendingFileChooser = callback;
                // Respect the HTML input accept attribute: photos use image/*,
                // while Restore uses application/json.
                String[] acceptTypes = params.getAcceptTypes();
                String mimeType = "*/*";
                if (acceptTypes != null) {
                    for (String type : acceptTypes) {
                        if (type != null && !type.trim().isEmpty()) {
                            mimeType = type.trim().split(",")[0].trim();
                            break;
                        }
                    }
                }
                if (mimeType.startsWith(".")) {
                    mimeType = ".json".equalsIgnoreCase(mimeType)
                            ? "application/json" : "*/*";
                }
                Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType(mimeType);
                intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,
                        params.getMode() == FileChooserParams.MODE_OPEN_MULTIPLE);
                try {
                    pendingChooserRequestCode = mimeType.startsWith("image/") ? OPEN_PHOTO_FILE : OPEN_RESTORE_FILE;
                    startActivityForResult(intent, pendingChooserRequestCode);
                    return true;
                } catch (Exception e) {
                    pendingFileChooser = null;
                    callback.onReceiveValue(null);
                    Toast.makeText(MainActivity.this, "Unable to open file picker", Toast.LENGTH_LONG).show();
                    return true;
                }
            }
        });
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        webView.addJavascriptInterface(new BackupBridge(), "VoyagesAndroid");
        setContentView(webView);
        webView.loadUrl("file:///android_asset/index.html");
    }

    private class BackupBridge {
        @JavascriptInterface
        public void saveBackup(String json) {
            runOnUiThread(() -> {
                if (json == null || json.isEmpty()) {
                    Toast.makeText(MainActivity.this, "No data to save", Toast.LENGTH_SHORT).show();
                    return;
                }
                pendingBackup = json;
                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("application/json");
                intent.putExtra(Intent.EXTRA_TITLE, "memories-backup.json");
                try {
                    startActivityForResult(intent, CREATE_BACKUP_FILE);
                } catch (Exception e) {
                    pendingBackup = null;
                    Toast.makeText(MainActivity.this, "Unable to open save dialog", Toast.LENGTH_LONG).show();
                }
            });
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == OPEN_RESTORE_FILE || requestCode == OPEN_PHOTO_FILE) {
            ValueCallback<Uri[]> callback = pendingFileChooser;
            pendingFileChooser = null;
            if (callback != null) {
                Uri uri = resultCode == RESULT_OK && data != null ? data.getData() : null;
                callback.onReceiveValue(uri == null ? null : new Uri[]{uri});
            }
            return;
        }
        if (requestCode != CREATE_BACKUP_FILE) return;
        String backup = pendingBackup;
        pendingBackup = null;
        if (resultCode != RESULT_OK || data == null || data.getData() == null || backup == null) return;
        try (OutputStream stream = getContentResolver().openOutputStream(data.getData(), "wt")) {
            if (stream == null) throw new Exception("Unable to open destination");
            stream.write(backup.getBytes(StandardCharsets.UTF_8));
            stream.flush();
            Toast.makeText(this, "Backup saved successfully", Toast.LENGTH_LONG).show();
        } catch (Exception e) {
            Toast.makeText(this, "Backup failed: " + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    @Override
    protected void onDestroy() {
        if (pendingFileChooser != null) pendingFileChooser.onReceiveValue(null);
        if (webView != null) webView.destroy();
        super.onDestroy();
    }
}
