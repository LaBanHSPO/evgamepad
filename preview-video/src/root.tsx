import {Composition, Folder} from 'remotion';
import {PreviewVideo} from './video';
import {IntroScene} from './scenes/intro-scene';
import {PreparationScene} from './scenes/preparation-scene';
import {ControlScene} from './scenes/control-scene';
import {SafetyScene} from './scenes/safety-scene';
import {CoachScene} from './scenes/coach-scene';
import {SupportScene} from './scenes/support-scene';
import {LearnScene} from './scenes/learn-scene';
import {ProcessScene} from './scenes/process-scene';
import {JournalScene} from './scenes/journal-scene';
import {DataScene} from './scenes/data-scene';
import {ClosingScene} from './scenes/closing-scene';

export const RemotionRoot = () => {
  return (
    <>
      <Folder name="Preview-Scenes">
        <Composition id="IntroScene" component={IntroScene} durationInFrames={210} fps={30} width={1920} height={1080} />
        <Composition id="PreparationScene" component={PreparationScene} durationInFrames={210} fps={30} width={1920} height={1080} />
        <Composition id="ControlScene" component={ControlScene} durationInFrames={210} fps={30} width={1920} height={1080} />
        <Composition id="SafetyScene" component={SafetyScene} durationInFrames={210} fps={30} width={1920} height={1080} />
        <Composition id="CoachScene" component={CoachScene} durationInFrames={210} fps={30} width={1920} height={1080} />
        <Composition id="SupportScene" component={SupportScene} durationInFrames={210} fps={30} width={1920} height={1080} />
        <Composition id="LearnScene" component={LearnScene} durationInFrames={210} fps={30} width={1920} height={1080} />
        <Composition id="ProcessScene" component={ProcessScene} durationInFrames={210} fps={30} width={1920} height={1080} />
        <Composition id="JournalScene" component={JournalScene} durationInFrames={210} fps={30} width={1920} height={1080} />
        <Composition id="DataScene" component={DataScene} durationInFrames={210} fps={30} width={1920} height={1080} />
        <Composition id="ClosingScene" component={ClosingScene} durationInFrames={210} fps={30} width={1920} height={1080} />
      </Folder>
      <Composition
        id="EveningForexGoldGamepadPreview"
        component={PreviewVideo}
        durationInFrames={2160}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
