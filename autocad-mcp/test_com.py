"""Test COM connection from a FRESH Python process."""
import win32com.client
import pythoncom


def main():
    try:
        app = win32com.client.GetActiveObject("AutoCAD.Application")
        print(f"Version: {app.Version}")
        print(f"Documents: {app.Documents.Count}")
        doc = app.ActiveDocument
        print(f"Active: {doc.Name} ({doc.FullName})")
        print(f"Entities: {doc.ModelSpace.Count}")
        print(f"Active layer: {doc.ActiveLayer.Name}")
    except pythoncom.com_error as e:
        print(f"COM error: {e}")
    except Exception as e:
        print(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
