package com.sofiamagalhaes.voyages;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import java.io.OutputStream;

public class MainActivity extends Activity {
    private static final int PHOTO_REQUEST = 301;
    private static final int BACKUP_REQUEST = 302;
    private WebView webView;
    private ValueCallback<Uri[]> photoCallback;
    private byte[] pendingBackup;

    public class BackupBridge {
        @JavascriptInterface
        public void save(String name, String base64) {
            try {
                final byte[] bytes = Base64.decode(base64, Base64.DEFAULT);
                final String filename = (name != null && name.matches("[a-zA-Z0-9._ -]{1,120}"))
                    ? name : "memories-backup.json";
                runOnUiThread(() -> {
                    pendingBackup = bytes;
                    Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                    intent.addCategory(Intent.CATEGORY_OPENABLE);
                    intent.setType("application/json");
                    intent.putExtra(Intent.EXTRA_TITLE, filename);
                    startActivityForResult(intent, BACKUP_REQUEST);
                });
            } catch (Exception ignored) { }
        }
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        webView = new WebView(this);
        setContentView(webView);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        webView.addJavascriptInterface(new BackupBridge(), "MemoriesAndroid");
        webView.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView view,
                    ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (photoCallback != null) photoCallback.onReceiveValue(null);
                photoCallback = callback;
                try {
                    Intent intent = params.createIntent();
                    startActivityForResult(intent, PHOTO_REQUEST);
                    return true;
                } catch (Exception error) {
                    photoCallback = null;
                    return false;
                }
            }
        });
        webView.setWebViewClient(new WebViewClient() {
            @Override public void onPageFinished(WebView view, String url) {
                // WebView cannot download blob: links itself. Forward JSON backup
                // downloads to Android's document picker, preserving user choice.
                String js = "(function(){if(window.__memoriesBackupHook)return;" +
                    "window.__memoriesBackupHook=true;" +
                    "document.addEventListener('click',function(e){" +
                    "var a=e.target.closest&&e.target.closest('a[download]');" +
                    "if(!a||!a.href||!a.href.startsWith('blob:'))return;" +
                    "var name=a.getAttribute('download')||'memories-backup.json';" +
                    "if(!/\\.json$/i.test(name))return;" +
                    "e.preventDefault();" +
                    "fetch(a.href).then(function(r){return r.blob()}).then(function(b){" +
                    "var reader=new FileReader();" +
                    "reader.onloadend=function(){var v=String(reader.result||'');" +
                    "window.MemoriesAndroid.save(name,v.split(',')[1]||'')};" +
                    "reader.readAsDataURL(b);" +
                    "}).catch(function(){alert('Backup could not be saved')});" +
                    "},true);" +
                    "})();";
                view.evaluateJavascript(js, null);
            }
        });
        webView.loadUrl("file:///android_asset/index.html");
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == PHOTO_REQUEST) {
            if (photoCallback != null) {
                photoCallback.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result, data));
                photoCallback = null;
            }
        } else if (request == BACKUP_REQUEST) {
            if (result == RESULT_OK && data != null && data.getData() != null && pendingBackup != null) {
                try (OutputStream out = getContentResolver().openOutputStream(data.getData())) {
                    if (out != null) out.write(pendingBackup);
                } catch (Exception ignored) { }
            }
            pendingBackup = null;
        }
    }

    @Override public void onBackPressed() {
        if (webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }
}
