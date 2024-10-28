import QtQuick
import QtQuick.Controls

ApplicationWindow {
    title: 'Test'
    visible: true

    ListView {
        model: backend.window
        focus: true
        anchors.fill: parent

        delegate: Item {
            Accessible.name: series.key
            Accessible.role: Accessible.ListItem

            Text {
                text: series.key
            }
            Keys.onPressed: {
                if (event.key === Qt.Key_Space) {
                    event.accepted = true;
                    series.play();
                }
            }
        }

        Keys.onPressed: {
            if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                event.accepted = true;
                backend.window.play();
            }
        }
    }
}
