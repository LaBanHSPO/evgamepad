import {TransitionSeries, linearTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {slide} from '@remotion/transitions/slide';
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

export const PreviewVideo = () => {
  return (
    <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={210} name="Meet the project">
        <IntroScene />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({durationInFrames: 15})} />
      <TransitionSeries.Sequence durationInFrames={210} name="Prepare the evening">
        <PreparationScene />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={slide({direction: 'from-right'})} timing={linearTiming({durationInFrames: 15})} />
      <TransitionSeries.Sequence durationInFrames={210} name="Trade with intent">
        <ControlScene />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={slide({direction: 'from-right'})} timing={linearTiming({durationInFrames: 15})} />
      <TransitionSeries.Sequence durationInFrames={210} name="Demo-first safety">
        <SafetyScene />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({durationInFrames: 15})} />
      <TransitionSeries.Sequence durationInFrames={210} name="Guidance beside you">
        <CoachScene />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={slide({direction: 'from-bottom'})} timing={linearTiming({durationInFrames: 15})} />
      <TransitionSeries.Sequence durationInFrames={210} name="Voice and adaptive friction">
        <SupportScene />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({durationInFrames: 15})} />
      <TransitionSeries.Sequence durationInFrames={210} name="Replay the decision">
        <LearnScene />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({durationInFrames: 15})} />
      <TransitionSeries.Sequence durationInFrames={210} name="Score the process">
        <ProcessScene />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={slide({direction: 'from-right'})} timing={linearTiming({durationInFrames: 15})} />
      <TransitionSeries.Sequence durationInFrames={210} name="Build the journal">
        <JournalScene />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({durationInFrames: 15})} />
      <TransitionSeries.Sequence durationInFrames={210} name="Own the record">
        <DataScene />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({durationInFrames: 15})} />
      <TransitionSeries.Sequence durationInFrames={210} name="Process over outcome">
        <ClosingScene />
      </TransitionSeries.Sequence>
    </TransitionSeries>
  );
};
