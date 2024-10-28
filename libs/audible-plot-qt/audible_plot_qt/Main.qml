import QtQuick
import QtQuick.Controls

ApplicationWindow {
    title: 'Test'
    visible: true

    property var position: 0
    property var window: backend.window

    ListView {
        model: window
        focus: true
        anchors.fill: parent

        delegate: Item {
            Accessible.name: series.key + "=" + series.at(position)
            Accessible.role: Accessible.ListItem

            Text {
                text: series.key
            }
            Keys.onPressed: event => {
                if (event.key === Qt.Key_Space) {
                    event.accepted = true;
                    series.play();
                } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                    event.accepted = true;
                    window.play();
                } else if (event.key === Qt.Key_Left) {
                    event.accepted = true;
                    if (position == 0) {
                        backend.moveLeft();
                        return;
                    }
                    position = position - 1;
                } else if (event.key == Qt.Key_Right) {
                    event.accepted = true;
                    if (position === series.size - 1) {
                        backend.moveRight();
                        return;
                    }
                    position = position + 1;
                }
            }
        }
    }

    Connections {
        target: backend

        function onSliceChanged(slice) {
            console.log("New window starts at " + slice.start);
        }
    }
}
