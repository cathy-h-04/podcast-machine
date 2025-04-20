import { useEffect } from "react";
import { useDaily } from "@daily-co/daily-react";
import { CameraSettings } from "../CameraSettings";

import { Call } from "../Call";

export const CallScreen = ({
  conversation,
  handleEnd,
}: {
  conversation: any;
  handleEnd: () => void;
}) => {
  const daily = useDaily();

  useEffect(() => {
    if (conversation && daily) {
      const { conversation_url } = conversation;
      daily.join({
        url: conversation_url,
      });
    }
  }, [daily, conversation]);

  const handleLeave = async () => {
    await daily?.leave();
    handleEnd();
  };

  return (
    <div>
      <Call />
      <CameraSettings actionLabel="Leave Call" onAction={handleLeave} />
    </div>
  );
};
